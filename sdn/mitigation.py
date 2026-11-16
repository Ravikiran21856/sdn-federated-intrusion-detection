"""
Reactive SDN Policy and Mitigation Engine.
Converts zero-day anomaly alerts into OpenFlow FlowMod drop or quarantine instructions.
"""

import uuid
from typing import Dict, Any
from sdn.switch import FlowRule
from config import SDNConfig


class SDNMitigationEngine:
    """
    Transforms detection alerts into OpenFlow-compliant flow rules.
    """

    def __init__(self, config: SDNConfig = SDNConfig()):
        self.config = config

    def generate_mitigation_rule(
        self, flow_meta: Dict[str, Any], action: str = "DROP"
    ) -> FlowRule:
        """
        Creates an OpenFlow rule to block or quarantine an anomalous flow.
        Matches 5-tuple: src_ip, dst_ip, protocol, dst_port.
        """
        match = {
            "src_ip": flow_meta.get("src_ip", "0.0.0.0"),
            "dst_ip": flow_meta.get("dst_ip", "0.0.0.0"),
            "protocol": flow_meta.get("protocol", "TCP"),
            "dst_port": flow_meta.get("dst_port", 80)
        }

        rule_id = f"mitigate_{uuid.uuid4().hex[:8]}"

        rule = FlowRule(
            rule_id=rule_id,
            priority=self.config.hard_drop_priority,
            match=match,
            action=action,
            idle_timeout=self.config.idle_timeout,
            hard_timeout=self.config.hard_timeout
        )
        return rule
