"""
SDN Controller Interface (Ryu / ONOS Abstraction).
Manages telemetry ingestion, runs real-time anomaly inference, and injects reactive mitigation rules.
"""

import time
import torch
import numpy as np
from typing import List, Dict, Any, Tuple

from sdn.switch import OpenFlowSwitch
from sdn.mitigation import SDNMitigationEngine
from models.autoencoder import FlowVAE
from data.preprocessor import FlowDataPreprocessor
from config import SDNConfig


class DistributedSDNController:
    """
    Simulates an SDN Controller (such as Ryu or ONOS) operating in a specific network domain.
    """

    def __init__(
        self,
        domain_id: int,
        name: str,
        detection_model: FlowVAE,
        preprocessor: FlowDataPreprocessor,
        anomaly_threshold: float,
        sdn_config: SDNConfig = SDNConfig(),
        device: str = "cpu"
    ):
        self.domain_id = domain_id
        self.name = name
        self.model = detection_model
        self.preprocessor = preprocessor
        self.anomaly_threshold = anomaly_threshold
        self.sdn_config = sdn_config
        self.device = device

        self.mitigation_engine = SDNMitigationEngine(sdn_config)
        self.switches: Dict[str, OpenFlowSwitch] = {}
        self.incident_log: List[Dict[str, Any]] = []

    def register_switch(self, switch: OpenFlowSwitch):
        self.switches[switch.dpid] = switch

    def inspect_and_mitigate(
        self, flow_features: np.ndarray, flow_metadata: Dict[str, Any], switch_dpid: str
    ) -> Dict[str, Any]:
        """
        Receives flow telemetry, computes anomaly score via VAE reconstruction loss,
        and dynamically pushes OpenFlow flow rules if an anomaly or zero-day is detected.
        """
        start_time = time.perf_counter()

        # Preprocess features
        norm_feat = self.preprocessor.transform(flow_features.reshape(1, -1))
        tensor_x = torch.tensor(norm_feat, dtype=torch.float32).to(self.device)

        # Anomaly scoring
        self.model.eval()
        with torch.no_grad():
            score = float(self.model.compute_anomaly_score(tensor_x).cpu().item())

        is_anomaly = score > self.anomaly_threshold
        mitigation_applied = False
        rule_installed = None

        if is_anomaly:
            rule = self.mitigation_engine.generate_mitigation_rule(flow_metadata, action="DROP")
            target_switch = self.switches.get(switch_dpid)
            if target_switch:
                target_switch.add_flow_rule(rule)
                mitigation_applied = True
                rule_installed = rule.rule_id

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        record = {
            "timestamp": time.time(),
            "domain_id": self.domain_id,
            "switch_dpid": switch_dpid,
            "anomaly_score": score,
            "threshold": self.anomaly_threshold,
            "is_anomaly": is_anomaly,
            "mitigation_applied": mitigation_applied,
            "rule_installed": rule_installed,
            "latency_ms": latency_ms,
            "flow_meta": flow_metadata
        }
        self.incident_log.append(record)
        return record
