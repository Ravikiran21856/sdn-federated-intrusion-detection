"""
Central Federated Aggregation Server.
Coordinates communication rounds across distributed SDN controllers.
"""

import copy
import torch
import numpy as np
from typing import List, Dict, Any, Tuple

from models.autoencoder import FlowVAE
from federated.client import SDNClient
from federated.secure_agg import SecureAggregatorHelper
from config import ModelConfig, FederatedConfig


class FederatedServer:
    """
    Orchestrates global model aggregation (FedAvg / FedProx) across SDN controller clients.
    """

    def __init__(
        self,
        clients: List[SDNClient],
        model_config: ModelConfig = ModelConfig(),
        fed_config: FederatedConfig = FederatedConfig(),
        device: str = "cpu"
    ):
        self.clients = clients
        self.model_config = model_config
        self.fed_config = fed_config
        self.device = device

        self.global_model = FlowVAE(model_config).to(self.device)
        self.sec_agg = SecureAggregatorHelper(
            clip_norm=fed_config.dp_clip_norm,
            noise_std=fed_config.dp_noise_std
        )
        self.round_history = []
        self.global_threshold = None

    def get_global_weights(self) -> Dict[str, torch.Tensor]:
        return copy.deepcopy(self.global_model.state_dict())

    def aggregate_weights(
        self, client_updates: List[Tuple[Dict[str, torch.Tensor], int]]
    ) -> Dict[str, torch.Tensor]:
        """
        Performs weighted Federated Averaging (FedAvg):
        W_global = sum( (n_k / N_total) * W_k )
        """
        total_samples = sum(n_samples for _, n_samples in client_updates)
        global_state = self.get_global_weights()
        aggregated_state = {k: torch.zeros_like(v, dtype=torch.float32) for k, v in global_state.items()}

        for client_state, n_samples in client_updates:
            weight = n_samples / total_samples

            # Apply DP clipping and noise if configured
            if self.fed_config.dp_noise_std > 0 or self.fed_config.dp_clip_norm < 100.0:
                client_state = self.sec_agg.sanitize_weights(client_state, global_state)

            for k in aggregated_state:
                aggregated_state[k] += weight * client_state[k].float()

        # Convert back to target types
        for k in aggregated_state:
            aggregated_state[k] = aggregated_state[k].to(global_state[k].dtype)

        return aggregated_state

    def train_round(self, round_num: int) -> float:
        """
        Executes one complete communication round:
        Broadcast -> Local Training -> Aggregation -> Broadcast Back.
        """
        global_weights = self.get_global_weights()
        client_updates = []
        client_losses = []

        for client in self.clients:
            client.set_weights(global_weights)
            weights, n_samples, loss = client.train_round(global_weights)
            client_updates.append((weights, n_samples))
            client_losses.append(loss)

        # Aggregate updates
        new_global_weights = self.aggregate_weights(client_updates)
        self.global_model.load_state_dict(new_global_weights)

        avg_loss = float(np.mean(client_losses))
        self.round_history.append({
            "round": round_num,
            "avg_client_loss": avg_loss,
            "client_losses": client_losses
        })
        return avg_loss

    def train(self) -> List[Dict[str, Any]]:
        """
        Runs the full federated learning lifecycle over configured rounds.
        """
        print(f"[*] Starting Federated Training ({self.fed_config.num_rounds} rounds, {len(self.clients)} SDN Domains)...")
        for r in range(1, self.fed_config.num_rounds + 1):
            avg_loss = self.train_round(r)
            print(f"  [Round {r:02d}/{self.fed_config.num_rounds:02d}] Global Avg Reconstruction Loss: {avg_loss:.5f}")

        # Broadcast finalized model to all clients
        final_weights = self.get_global_weights()
        for client in self.clients:
            client.set_weights(final_weights)

        return self.round_history

    def calibrate_global_threshold(self, percentile: float = 95.0) -> float:
        """
        Aggregates local client thresholds to establish a federated anomaly cutoff.
        """
        thresholds = [client.calibrate_anomaly_threshold(percentile) for client in self.clients]
        self.global_threshold = float(np.mean(thresholds))
        return self.global_threshold
