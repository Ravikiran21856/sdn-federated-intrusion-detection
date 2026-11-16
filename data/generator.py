"""
Synthetic SDN Network Flow Generator.
Simulates realistic benign network flows, known attack signatures, and novel zero-day exploits.
"""

import numpy as np
from typing import Tuple, Dict, Any, List
from config import DataConfig


class SDNTrafficGenerator:
    """
    Generates realistic SDN flow metrics based on OpenFlow telemetry conventions
    (inspired by InSDN and CIC-IDS2017 datasets).
    """

    def __init__(self, config: DataConfig = DataConfig()):
        self.config = config
        self.rng = np.random.RandomState(config.seed)

    def _generate_benign_flows(self, n_samples: int, domain_bias: int = 0) -> np.ndarray:
        """
        Generate normal network traffic.
        domain_bias alters mean flow sizes to simulate non-IID conditions across domains
        (e.g., Domain 0 = Enterprise Workstations, Domain 1 = Data Center, Domain 2 = IoT Edge).
        """
        # Feature order matches DataConfig.feature_names (16 features):
        # [flow_duration, fwd_pkts, bwd_pkts, fwd_bytes, bwd_bytes, bytes_sec,
        #  pkts_sec, iat_mean, iat_std, syn_ratio, fin_ratio, rst_ratio,
        #  ack_ratio, fwd_hdr_len, bwd_hdr_len, flow_symmetry]

        if domain_bias == 0:  # Enterprise: Moderate bursty web/email
            duration = self.rng.exponential(scale=12.0, size=(n_samples, 1)) + 0.1
            fwd_pkts = self.rng.poisson(lam=18, size=(n_samples, 1)) + 1
            bwd_pkts = self.rng.poisson(lam=22, size=(n_samples, 1)) + 1
            fwd_bytes = fwd_pkts * self.rng.normal(loc=550, scale=80, size=(n_samples, 1)).clip(min=64)
            bwd_bytes = bwd_pkts * self.rng.normal(loc=980, scale=120, size=(n_samples, 1)).clip(min=64)
        elif domain_bias == 1:  # Data Center: High throughput, high packets, low latency
            duration = self.rng.exponential(scale=4.0, size=(n_samples, 1)) + 0.05
            fwd_pkts = self.rng.poisson(lam=65, size=(n_samples, 1)) + 5
            bwd_pkts = self.rng.poisson(lam=75, size=(n_samples, 1)) + 5
            fwd_bytes = fwd_pkts * self.rng.normal(loc=1200, scale=100, size=(n_samples, 1)).clip(min=128)
            bwd_bytes = bwd_pkts * self.rng.normal(loc=1420, scale=80, size=(n_samples, 1)).clip(min=128)
        else:  # IoT / Edge: Low packet count, periodic IAT, low bytes
            duration = self.rng.exponential(scale=25.0, size=(n_samples, 1)) + 1.0
            fwd_pkts = self.rng.poisson(lam=4, size=(n_samples, 1)) + 1
            bwd_pkts = self.rng.poisson(lam=3, size=(n_samples, 1)) + 1
            fwd_bytes = fwd_pkts * self.rng.normal(loc=180, scale=40, size=(n_samples, 1)).clip(min=40)
            bwd_bytes = bwd_pkts * self.rng.normal(loc=120, scale=30, size=(n_samples, 1)).clip(min=40)

        total_bytes = fwd_bytes + bwd_bytes
        total_pkts = fwd_pkts + bwd_pkts
        bytes_sec = total_bytes / duration
        pkts_sec = total_pkts / duration

        iat_mean = duration / (total_pkts + 1e-5)
        iat_std = iat_mean * self.rng.uniform(0.1, 0.4, size=(n_samples, 1))

        # TCP Flag distribution for legitimate traffic (mostly ACK, balanced SYN/FIN)
        syn_ratio = self.rng.uniform(0.02, 0.08, size=(n_samples, 1))
        fin_ratio = self.rng.uniform(0.02, 0.08, size=(n_samples, 1))
        rst_ratio = self.rng.uniform(0.00, 0.02, size=(n_samples, 1))
        ack_ratio = self.rng.uniform(0.85, 0.98, size=(n_samples, 1))

        fwd_hdr_len = fwd_pkts * 32.0
        bwd_hdr_len = bwd_pkts * 32.0
        flow_symmetry = np.minimum(fwd_pkts, bwd_pkts) / (np.maximum(fwd_pkts, bwd_pkts) + 1e-5)

        features = np.hstack([
            duration, fwd_pkts, bwd_pkts, fwd_bytes, bwd_bytes, bytes_sec,
            pkts_sec, iat_mean, iat_std, syn_ratio, fin_ratio, rst_ratio,
            ack_ratio, fwd_hdr_len, bwd_hdr_len, flow_symmetry
        ])
        return features

    def _generate_known_attacks(self, n_samples: int) -> np.ndarray:
        """
        Known attacks: SYN Flood, PortScan, and Standard Brute Force.
        Characteristic: Extreme SYN ratio, asymmetric flows, or high packet rates with tiny payloads.
        """
        duration = self.rng.exponential(scale=2.0, size=(n_samples, 1)) + 0.01
        fwd_pkts = self.rng.poisson(lam=120, size=(n_samples, 1)) + 10
        bwd_pkts = self.rng.poisson(lam=1, size=(n_samples, 1))  # Server drops or SYN-ACK unacknowledged
        fwd_bytes = fwd_pkts * 64.0  # minimal TCP header payload
        bwd_bytes = bwd_pkts * 40.0

        total_bytes = fwd_bytes + bwd_bytes
        total_pkts = fwd_pkts + bwd_pkts
        bytes_sec = total_bytes / duration
        pkts_sec = total_pkts / duration

        iat_mean = duration / (total_pkts + 1e-5)
        iat_std = iat_mean * 0.05  # highly periodic attack tool

        syn_ratio = self.rng.uniform(0.85, 1.0, size=(n_samples, 1))  # Classic SYN flood signature
        fin_ratio = self.rng.uniform(0.0, 0.02, size=(n_samples, 1))
        rst_ratio = self.rng.uniform(0.10, 0.40, size=(n_samples, 1))
        ack_ratio = self.rng.uniform(0.01, 0.15, size=(n_samples, 1))

        fwd_hdr_len = fwd_pkts * 20.0
        bwd_hdr_len = bwd_pkts * 20.0
        flow_symmetry = np.minimum(fwd_pkts, bwd_pkts) / (np.maximum(fwd_pkts, bwd_pkts) + 1e-5)

        features = np.hstack([
            duration, fwd_pkts, bwd_pkts, fwd_bytes, bwd_bytes, bytes_sec,
            pkts_sec, iat_mean, iat_std, syn_ratio, fin_ratio, rst_ratio,
            ack_ratio, fwd_hdr_len, bwd_hdr_len, flow_symmetry
        ])
        return features

    def _generate_zero_day_exploits(self, n_samples: int) -> np.ndarray:
        """
        Zero-Day Exploits: Novel attacks never seen in signature databases.
        Examples:
          1. Slow-rate Stealth DoS (Low packet rate, extremely prolonged IAT, connection exhaustion)
          2. DNS/ICMP Covert Tunneling (Unusual payload symmetry, anomalous header sizes, jittered IAT)
          3. Micro-burst Buffer Overflow (High payload density with abrupt termination)
        """
        half = n_samples // 2
        rem = n_samples - half

        # Sub-type 1: Slow-rate stealth exhaustion (Slowloris variant)
        duration_1 = self.rng.uniform(180.0, 600.0, size=(half, 1))
        fwd_pkts_1 = self.rng.uniform(8, 25, size=(half, 1))
        bwd_pkts_1 = self.rng.uniform(4, 15, size=(half, 1))
        fwd_bytes_1 = fwd_pkts_1 * self.rng.uniform(20, 50, size=(half, 1))
        bwd_bytes_1 = bwd_pkts_1 * self.rng.uniform(30, 60, size=(half, 1))
        total_bytes_1 = fwd_bytes_1 + bwd_bytes_1
        total_pkts_1 = fwd_pkts_1 + bwd_pkts_1
        bytes_sec_1 = total_bytes_1 / duration_1
        pkts_sec_1 = total_pkts_1 / duration_1
        iat_mean_1 = duration_1 / (total_pkts_1 + 1e-5)
        iat_std_1 = iat_mean_1 * self.rng.uniform(0.7, 1.2, size=(half, 1))
        syn_ratio_1 = self.rng.uniform(0.04, 0.09, size=(half, 1))
        fin_ratio_1 = self.rng.uniform(0.00, 0.01, size=(half, 1))
        rst_ratio_1 = self.rng.uniform(0.05, 0.25, size=(half, 1))
        ack_ratio_1 = self.rng.uniform(0.70, 0.90, size=(half, 1))
        fwd_hdr_len_1 = fwd_pkts_1 * 40.0
        bwd_hdr_len_1 = bwd_pkts_1 * 40.0
        sym_1 = np.minimum(fwd_pkts_1, bwd_pkts_1) / (np.maximum(fwd_pkts_1, bwd_pkts_1) + 1e-5)

        feat_1 = np.hstack([
            duration_1, fwd_pkts_1, bwd_pkts_1, fwd_bytes_1, bwd_bytes_1, bytes_sec_1,
            pkts_sec_1, iat_mean_1, iat_std_1, syn_ratio_1, fin_ratio_1, rst_ratio_1,
            ack_ratio_1, fwd_hdr_len_1, bwd_hdr_len_1, sym_1
        ])

        # Sub-type 2: Covert Channel Exfiltration (High payload variance, strange header-to-payload ratio)
        duration_2 = self.rng.uniform(1.0, 15.0, size=(rem, 1))
        fwd_pkts_2 = self.rng.uniform(30, 90, size=(rem, 1))
        bwd_pkts_2 = self.rng.uniform(5, 15, size=(rem, 1))
        fwd_bytes_2 = fwd_pkts_2 * self.rng.uniform(1450, 1500, size=(rem, 1))  # Max MTU stuffing
        bwd_bytes_2 = bwd_pkts_2 * self.rng.uniform(40, 70, size=(rem, 1))
        total_bytes_2 = fwd_bytes_2 + bwd_bytes_2
        total_pkts_2 = fwd_pkts_2 + bwd_pkts_2
        bytes_sec_2 = total_bytes_2 / duration_2
        pkts_sec_2 = total_pkts_2 / duration_2
        iat_mean_2 = duration_2 / (total_pkts_2 + 1e-5)
        iat_std_2 = iat_mean_2 * self.rng.uniform(0.01, 0.1, size=(rem, 1))
        syn_ratio_2 = self.rng.uniform(0.01, 0.03, size=(rem, 1))
        fin_ratio_2 = self.rng.uniform(0.01, 0.03, size=(rem, 1))
        rst_ratio_2 = self.rng.uniform(0.00, 0.05, size=(rem, 1))
        ack_ratio_2 = self.rng.uniform(0.80, 0.95, size=(rem, 1))
        fwd_hdr_len_2 = fwd_pkts_2 * 20.0
        bwd_hdr_len_2 = bwd_pkts_2 * 20.0
        sym_2 = np.minimum(fwd_pkts_2, bwd_pkts_2) / (np.maximum(fwd_pkts_2, bwd_pkts_2) + 1e-5)

        feat_2 = np.hstack([
            duration_2, fwd_pkts_2, bwd_pkts_2, fwd_bytes_2, bwd_bytes_2, bytes_sec_2,
            pkts_sec_2, iat_mean_2, iat_std_2, syn_ratio_2, fin_ratio_2, rst_ratio_2,
            ack_ratio_2, fwd_hdr_len_2, bwd_hdr_len_2, sym_2
        ])

        return np.vstack([feat_1, feat_2])

    def generate_federated_environment(self) -> Dict[str, Any]:
        """
        Creates partitioned training data for each SDN domain client (benign baseline)
        and an unobserved evaluation test set containing benign, known attacks,
        and completely novel zero-day attacks.
        """
        clients_data = []
        for i in range(self.config.num_clients):
            # Each client has its own benign domain baseline (Non-IID)
            benign_data = self._generate_benign_flows(
                self.config.num_samples_per_client, domain_bias=i % 3
            )
            clients_data.append(benign_data)

        # Test set preparation:
        # Benign (50%), Known Attacks (25%), Zero-Day Exploits (25%)
        n_test = self.config.test_samples
        n_zero_day = int(n_test * self.config.zero_day_ratio_in_test)
        n_known = int(n_test * self.config.known_attack_ratio_in_test)
        n_benign_test = n_test - n_zero_day - n_known

        test_benign = np.vstack([
            self._generate_benign_flows(n_benign_test // 3, domain_bias=0),
            self._generate_benign_flows(n_benign_test // 3, domain_bias=1),
            self._generate_benign_flows(n_benign_test - 2 * (n_benign_test // 3), domain_bias=2)
        ])
        test_known = self._generate_known_attacks(n_known)
        test_zero_day = self._generate_zero_day_exploits(n_zero_day)

        test_features = np.vstack([test_benign, test_known, test_zero_day])
        # Labels: 0 = Benign, 1 = Known Attack, 2 = Zero-Day Exploit
        test_labels = np.array(
            [0] * len(test_benign) + [1] * len(test_known) + [2] * len(test_zero_day)
        )

        # Shuffle test set
        perm = self.rng.permutation(len(test_labels))
        test_features = test_features[perm]
        test_labels = test_labels[perm]

        return {
            "client_train_data": clients_data,
            "test_features": test_features,
            "test_labels": test_labels,
            "feature_names": self.config.feature_names
        }
