"""
Deep Variational Autoencoder (VAE) for Unsupervised Zero-Day Anomaly Detection.
Trained exclusively on benign flow distributions; unseen attack behaviors yield high reconstruction loss.
"""

import torch
import torch.nn as nn
from typing import Tuple
from config import ModelConfig


class FlowVAE(nn.Module):
    """
    Variational Autoencoder with reparameterization trick for network flow anomaly detection.
    """

    def __init__(self, config: ModelConfig = ModelConfig()):
        super(FlowVAE, self).__init__()
        self.config = config

        # Encoder: Input -> Hidden Layers -> Mu & LogVar
        encoder_layers = []
        in_dim = config.input_dim
        for h_dim in config.hidden_dims:
            encoder_layers.extend([
                nn.Linear(in_dim, h_dim),
                nn.BatchNorm1d(h_dim),
                nn.LeakyReLU(0.2),
                nn.Dropout(0.1)
            ])
            in_dim = h_dim
        self.encoder_backbone = nn.Sequential(*encoder_layers)

        self.fc_mu = nn.Linear(in_dim, config.latent_dim)
        self.fc_logvar = nn.Linear(in_dim, config.latent_dim)

        # Decoder: Latent -> Reconstructed Hidden -> Reconstructed Input
        decoder_layers = []
        latent_dim = config.latent_dim
        rev_hidden = list(reversed(config.hidden_dims))
        for h_dim in rev_hidden:
            decoder_layers.extend([
                nn.Linear(latent_dim, h_dim),
                nn.BatchNorm1d(h_dim),
                nn.LeakyReLU(0.2),
                nn.Dropout(0.1)
            ])
            latent_dim = h_dim
        decoder_layers.append(nn.Linear(latent_dim, config.input_dim))
        self.decoder = nn.Sequential(*decoder_layers)

    def encode(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.encoder_backbone(x)
        mu = self.fc_mu(h)
        logvar = self.fc_logvar(h)
        return mu, logvar

    def reparameterize(self, mu: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        return self.decoder(z)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar) if self.training else mu
        x_recon = self.decode(z)
        return x_recon, mu, logvar

    def compute_anomaly_score(self, x: torch.Tensor) -> torch.Tensor:
        """
        Computes per-sample reconstruction error (MSE) as anomaly metric.
        High error indicates flows deviating from learned benign topology.
        """
        self.eval()
        with torch.no_grad():
            x_recon, _, _ = self.forward(x)
            per_sample_mse = torch.mean((x - x_recon) ** 2, dim=1)
        return per_sample_mse
