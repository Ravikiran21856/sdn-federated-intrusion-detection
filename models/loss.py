"""
Loss Functions for Variational Autoencoder Anomaly Detection.
Implements Beta-VAE ELBO (Evidence Lower Bound) loss formulation.
"""

import torch
import torch.nn as nn
from typing import Tuple


class VAELoss(nn.Module):
    """
    Computes Beta-VAE loss:
    Loss = Reconstruction_Loss (MSE) + beta * KL_Divergence
    """

    def __init__(self, beta: float = 0.5):
        super(VAELoss, self).__init__()
        self.beta = beta
        self.mse = nn.MSELoss(reduction="mean")

    def forward(
        self, x_recon: torch.Tensor, x: torch.Tensor, mu: torch.Tensor, logvar: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        # Reconstruction loss (fidelity to normal flow behavior)
        recon_loss = self.mse(x_recon, x)

        # KL Divergence: D_KL( q(z|x) || p(z) ) where p(z) ~ N(0, I)
        kl_div = -0.5 * torch.mean(torch.sum(1 + logvar - mu.pow(2) - logvar.exp(), dim=1))

        # Total Beta-VAE ELBO
        total_loss = recon_loss + self.beta * kl_div

        return total_loss, recon_loss, kl_div
