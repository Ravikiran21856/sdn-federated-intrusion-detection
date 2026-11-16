"""
OpenFlow Switch Simulation (Open vSwitch / OVS Model).
Maintains flow table, matches ingress packets, tracks telemetry counters, and executes actions.
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class FlowRule:
    rule_id: str
    priority: int
    match: Dict[str, Any]  # e.g., {'src_ip': '...', 'dst_ip': '...', 'protocol': 'TCP', 'dst_port': 80}
    action: str  # 'FORWARD', 'DROP', 'QUARANTINE'
    created_at: float = field(default_factory=time.time)
    idle_timeout: int = 300
    hard_timeout: int = 600
    packet_count: int = 0
    byte_count: int = 0


class OpenFlowSwitch:
    """
    Emulates an OpenFlow 1.3 Data Plane Switch.
    """

    def __init__(self, dpid: str, name: str):
        self.dpid = dpid
        self.name = name
        self.flow_table: List[FlowRule] = []
        self.dropped_packets: int = 0
        self.quarantined_packets: int = 0
        self.forwarded_packets: int = 0

    def add_flow_rule(self, rule: FlowRule):
        """
        Installs an OpenFlow rule (OFPFC_ADD). Keeps table sorted by priority descending.
        """
        # Remove existing rule with identical match if exists
        self.flow_table = [r for r in self.flow_table if r.match != rule.match]
        self.flow_table.append(rule)
        self.flow_table.sort(key=lambda r: r.priority, reverse=True)

    def process_packet(self, packet: Dict[str, Any]) -> str:
        """
        Evaluates an incoming packet against the flow table.
        Returns the action taken: 'FORWARD', 'DROP', 'QUARANTINE', or 'TABLE_MISS'.
        """
        for rule in self.flow_table:
            match = True
            for k, v in rule.match.items():
                if packet.get(k) != v:
                    match = False
                    break

            if match:
                rule.packet_count += 1
                rule.byte_count += packet.get("length", 64)
                if rule.action == "DROP":
                    self.dropped_packets += 1
                    return "DROP"
                elif rule.action == "QUARANTINE":
                    self.quarantined_packets += 1
                    return "QUARANTINE"
                else:
                    self.forwarded_packets += 1
                    return "FORWARD"

        # Table miss -> Forwarded to controller via PACKET_IN
        self.forwarded_packets += 1
        return "TABLE_MISS"

    def get_flow_statistics(self) -> List[Dict[str, Any]]:
        """
        Emulates OFPST_FLOW_REPLY telemetry response.
        """
        stats = []
        now = time.time()
        for r in self.flow_table:
            duration = now - r.created_at
            stats.append({
                "rule_id": r.rule_id,
                "match": r.match,
                "action": r.action,
                "packet_count": r.packet_count,
                "byte_count": r.byte_count,
                "duration_sec": duration,
                "priority": r.priority
            })
        return stats
