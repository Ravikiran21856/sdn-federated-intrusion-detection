"""
Local Federated Client representing an SDN Controller Domain.
Conducts local model optimization on domain-specific flow baselines.
"""

import copy
import torch
from torch.utils.data import DataLoader
from typing import Dict, Any, Tuple
import numpy as np

from models.autoencoder import FlowVAE
from models.loss import VAELoss
from config import ModelConfig, FederatedConfig


class SDNClient:
    """
    Represents an edge/domain SDN controller running a local intrusion detection worker.
    """

    def __init__(
        self,
        client_id: int,
        dataloader: DataLoader,
        model_config: ModelConfig = ModelConfig(),
        fed_config: FederatedConfig = FederatedConfig(),
        device: str = "cpu"
    ):
        self.client_id = client_id
        self.dataloader = dataloader
        self.model_config = model_config
        self.fed_config = fed_config
        self.device = device

        self.model = FlowVAE(model_config).to(self.device)
        self.criterion = VAELoss(beta=model_config.beta)
        self.anomaly_threshold = None

    def set_weights(self, state_dict: Dict[str, torch.Tensor]):
        """
        Loads updated global weights received from the central FL aggregator.
        """
        self.model.load_state_dict(state_dict)

    def get_weights(self) -> Dict[str, torch.Tensor]:
        return copy.deepcopy(self.model.state_dict())

    def train_round(
        self, global_state_dict: Dict[str, torch.Tensor]
    ) -> Tuple[Dict[str, torch.Tensor], int, float]:
        """
        Trains the local VAE on local benign traffic for local_epochs.
        Applies FedProx proximal regularization if enabled: (mu/2) * ||w - w_global||^2
        """
        self.model.train()
        optimizer = torch.optim.Adam(
            self.model.parameters(),
            lr=self.model_config.learning_rate,
            weight_decay=self.model_config.weight_decay
        )

        global_params = [
            param.clone().detach().to(self.device) for param in self.model.parameters()
        ]

        total_loss_accum = 0.0
        total_batches = 0

        for epoch in range(self.fed_config.local_epochs):
            for batch in self.dataloader:
                x = batch[0].to(self.device) if isinstance(batch, (list, tuple)) else batch.to(self.device)

                optimizer.zero_grad()
                x_recon, mu, logvar = self.model(x)
                loss, _, _ = self.criterion(x_recon, x, mu, logvar)

                # Proximal term for FedProx (mitigates domain divergence on non-IID flows)
                if self.fed_config.aggregation_method == "fedprox" and self.fed_config.fedprox_mu > 0:
                    prox_loss = 0.0
                    for local_p, glob_p in zip(self.model.parameters(), global_params):
                        prox_loss += torch.sum((local_p - glob_p) ** 2)
                    loss += (self.fed_config.fedprox_mu / 2.0) * prox_loss

                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=5.0)
                optimizer.step()

                total_loss_accum += loss.item()
                total_batches += 1

        avg_loss = total_loss_accum / max(1, total_batches)
        n_samples = len(self.dataloader.dataset)
        return self.get_weights(), n_samples, avg_loss

    def calibrate_anomaly_threshold(self, percentile: float = 95.0) -> float:
        """
        Calculates the local anomaly threshold based on the reconstruction loss distribution
        of baseline normal flows. Any incoming flow exceeding this threshold is flagged.
        """
        self.model.eval()
        scores = []
        with torch.no_grad():
            for batch in self.dataloader:
                x = batch[0].to(self.device) if isinstance(batch, (list, tuple)) else batch.to(self.device)
                sample_scores = self.model.compute_anomaly_score(x)
                scores.extend(sample_scores.cpu().numpy().tolist())

        self.anomaly_threshold = float(np.percentile(scores, percentile))
        return self.anomaly_threshold
