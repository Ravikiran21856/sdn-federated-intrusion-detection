"""
System Configuration for Federated Zero-Day Exploit Detection in SDN Environments.
"""

import os
from dataclasses import dataclass, field
from typing import List

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DATA_DIR = os.path.join(BASE_DIR, "data")

os.makedirs(OUTPUT_DIR, exist_ok=True)


@dataclass
class ModelConfig:
    input_dim: int = 16
    hidden_dims: List[int] = field(default_factory=lambda: [64, 32])
    latent_dim: int = 16
    beta: float = 0.5  # Beta-VAE weight for KL divergence
    learning_rate: float = 1e-3
    weight_decay: float = 1e-5


@dataclass
class FederatedConfig:
    num_clients: int = 3  # Corresponds to 3 distinct SDN domains (e.g., Enterprise, Data Center, IoT/Edge)
    num_rounds: int = 10
    local_epochs: int = 4
    batch_size: int = 64
    aggregation_method: str = "fedprox"  # 'fedavg' or 'fedprox'
    fedprox_mu: float = 0.01  # Proximal regularization coefficient for non-IID traffic
    dp_clip_norm: float = 1.0  # Differential Privacy Gradient Clipping
    dp_noise_std: float = 0.001  # DP Gaussian noise multiplier (0 to disable)


@dataclass
class SDNConfig:
    polling_interval_sec: float = 2.0  # OpenFlow stats polling interval
    threshold_percentile: float = 95.0  # Adaptive reconstruction loss anomaly threshold
    hard_drop_priority: int = 65535  # Priority of installed reactive mitigation OpenFlow rule
    quarantine_vlan: int = 999  # VLAN for honeypot redirection
    idle_timeout: int = 300  # Flow table idle timeout (seconds)
    hard_timeout: int = 600  # Flow table hard timeout (seconds)


@dataclass
class DataConfig:
    num_clients: int = 3
    num_samples_per_client: int = 2500
    test_samples: int = 2000
    zero_day_ratio_in_test: float = 0.25
    known_attack_ratio_in_test: float = 0.25
    seed: int = 42
    feature_names: List[str] = field(default_factory=lambda: [
        "flow_duration",
        "total_fwd_packets",
        "total_bwd_packets",
        "total_fwd_bytes",
        "total_bwd_bytes",
        "flow_bytes_per_sec",
        "flow_packets_per_sec",
        "packet_iat_mean",
        "packet_iat_std",
        "syn_flag_ratio",
        "fin_flag_ratio",
        "rst_flag_ratio",
        "ack_flag_ratio",
        "fwd_header_len",
        "bwd_header_len",
        "flow_symmetry_ratio"
    ])
