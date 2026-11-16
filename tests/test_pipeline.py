"""
Unit and Integration Tests for Federated Zero-Day Intrusion Detection Pipeline.
"""

import unittest
import numpy as np
import torch
import os

from config import ModelConfig, FederatedConfig, SDNConfig, DataConfig
from data.generator import SDNTrafficGenerator
from data.preprocessor import FlowDataPreprocessor
from models.autoencoder import FlowVAE
from models.loss import VAELoss
from federated.client import SDNClient
from federated.server import FederatedServer
from federated.secure_agg import SecureAggregatorHelper
from sdn.switch import OpenFlowSwitch, FlowRule
from sdn.mitigation import SDNMitigationEngine
from evaluation.metrics import IDSEvaluator


class TestFederatedSDNPipeline(unittest.TestCase):

    def setUp(self):
        self.data_cfg = DataConfig(num_clients=2, num_samples_per_client=100, test_samples=100)
        self.model_cfg = ModelConfig(input_dim=16, hidden_dims=[32, 16], latent_dim=8)
        self.sdn_cfg = SDNConfig()
        self.fed_cfg = FederatedConfig(num_clients=2, num_rounds=2, local_epochs=1)

    def test_data_generation(self):
        generator = SDNTrafficGenerator(self.data_cfg)
        env = generator.generate_federated_environment()

        self.assertEqual(len(env["client_train_data"]), 2)
        self.assertEqual(env["client_train_data"][0].shape[1], 16)
        self.assertFalse(np.isnan(env["client_train_data"][0]).any())
        self.assertEqual(len(env["test_labels"]), 100)
        self.assertTrue(set(env["test_labels"]).issubset({0, 1, 2}))

    def test_preprocessor(self):
        preprocessor = FlowDataPreprocessor()
        dummy_data = np.random.randn(50, 16) * 10.0 + 5.0
        norm = preprocessor.fit_transform(dummy_data)

        self.assertEqual(norm.shape, (50, 16))
        self.assertTrue(np.allclose(np.mean(norm, axis=0), 0.0, atol=1e-5))

    def test_vae_model(self):
        vae = FlowVAE(self.model_cfg)
        x = torch.randn(8, 16)
        x_recon, mu, logvar = vae(x)

        self.assertEqual(x_recon.shape, (8, 16))
        self.assertEqual(mu.shape, (8, self.model_cfg.latent_dim))
        self.assertEqual(logvar.shape, (8, self.model_cfg.latent_dim))

        scores = vae.compute_anomaly_score(x)
        self.assertEqual(scores.shape, (8,))
        self.assertTrue(torch.all(scores >= 0))

    def test_secure_agg(self):
        sec = SecureAggregatorHelper(clip_norm=1.0, noise_std=0.01)
        w_global = {"weight": torch.ones(5, 5)}
        w_client = {"weight": torch.ones(5, 5) * 5.0}  # Large diff

        sanitized = sec.sanitize_weights(w_client, w_global)
        diff = torch.norm(sanitized["weight"] - w_global["weight"])
        # Delta should be clipped close to 1.0 + slight noise
        self.assertAlmostEqual(float(diff), 1.0, delta=0.2)

    def test_sdn_flow_mitigation(self):
        switch = OpenFlowSwitch(dpid="00:00:00:00:00:01", name="s1")
        mitigation = SDNMitigationEngine(self.sdn_cfg)

        meta = {"src_ip": "10.0.0.99", "dst_ip": "192.168.1.1", "protocol": "TCP", "dst_port": 80}
        rule = mitigation.generate_mitigation_rule(meta, action="DROP")
        switch.add_flow_rule(rule)

        # Matching packet
        pkt = {"src_ip": "10.0.0.99", "dst_ip": "192.168.1.1", "protocol": "TCP", "dst_port": 80, "length": 64}
        action = switch.process_packet(pkt)
        self.assertEqual(action, "DROP")
        self.assertEqual(switch.dropped_packets, 1)

        # Non-matching packet
        benign_pkt = {"src_ip": "10.0.0.1", "dst_ip": "192.168.1.1", "protocol": "TCP", "dst_port": 80, "length": 64}
        action2 = switch.process_packet(benign_pkt)
        self.assertEqual(action2, "TABLE_MISS")

    def test_metrics_evaluator(self):
        y_true = np.array([0, 0, 1, 1, 2, 2])
        # Higher scores for attacks
        scores = np.array([0.1, 0.2, 0.8, 0.9, 0.85, 0.95])
        res = IDSEvaluator.evaluate(y_true, scores, threshold=0.5)

        self.assertEqual(res["roc_auc"], 1.0)
        self.assertEqual(res["zero_day_detection_rate"], 1.0)
        self.assertEqual(res["known_attack_detection_rate"], 1.0)
        self.assertEqual(res["false_positive_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
