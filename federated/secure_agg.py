"""
Privacy & Security Extensions for Federated Aggregation.
Implements Differential Privacy (DP) gradient/weight clipping and noise injection.
"""

import torch
from typing import Dict


class SecureAggregatorHelper:
    """
    Applies Local Differential Privacy (LDP) constraints to client weight updates
    to prevent inference attacks regarding local SDN topology or user traffic.
    """

    def __init__(self, clip_norm: float = 1.0, noise_std: float = 0.001):
        self.clip_norm = clip_norm
        self.noise_std = noise_std

    def sanitize_weights(
        self, client_state_dict: Dict[str, torch.Tensor], global_state_dict: Dict[str, torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        """
        Calculates delta (w_local - w_global), clips L2 norm to clip_norm,
        adds Gaussian noise, and reconstructs sanitized local weights.
        """
        sanitized_state = {}
        # Calculate total L2 norm of the difference vector
        total_norm_sq = 0.0
        deltas = {}
        for key in client_state_dict:
            delta = client_state_dict[key].float() - global_state_dict[key].float()
            deltas[key] = delta
            total_norm_sq += torch.sum(delta ** 2).item()

        total_norm = (total_norm_sq ** 0.5) + 1e-9
        clip_coeff = min(1.0, self.clip_norm / total_norm)

        for key in client_state_dict:
            clipped_delta = deltas[key] * clip_coeff
            if self.noise_std > 0:
                noise = torch.randn_like(clipped_delta) * self.noise_std
                clipped_delta = clipped_delta + noise
            sanitized_state[key] = (global_state_dict[key].float() + clipped_delta).to(
                client_state_dict[key].dtype
            )

        return sanitized_state
