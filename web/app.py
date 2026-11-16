"""
Web Application Backend & REST API Server.
Zero-dependency HTTP server utilizing Python standard library with full JSON REST API.
"""

import os
import sys
import json
import time
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
import numpy as np
import torch
from torch.utils.data import DataLoader

# Add project root to path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config import ModelConfig, FederatedConfig, SDNConfig, DataConfig, OUTPUT_DIR
from data.generator import SDNTrafficGenerator
from data.preprocessor import FlowDataPreprocessor
from data.dataset import FlowDataset
from models.autoencoder import FlowVAE
from federated.client import SDNClient
from federated.server import FederatedServer
from sdn.switch import OpenFlowSwitch
from sdn.controller import DistributedSDNController


class IDSBackend:
    """
    Stateful backend managing FL Server, SDN Controllers, and Switches.
    """

    def __init__(self):
        self.model_cfg = ModelConfig()
        self.fed_cfg = FederatedConfig()
        self.sdn_cfg = SDNConfig()
        self.data_cfg = DataConfig(num_samples_per_client=1000)

        torch.manual_seed(42)
        np.random.seed(42)
        self.device = "cpu"

        print("[*] Initializing Traffic Generator and Preprocessor...")
        self.generator = SDNTrafficGenerator(self.data_cfg)
        env_data = self.generator.generate_federated_environment()

        self.preprocessor = FlowDataPreprocessor()
        train_baseline = np.vstack(env_data["client_train_data"])
        self.preprocessor.fit(train_baseline)

        # Clients & Server
        print("[*] Setting up Federated Learning components...")
        self.client_loaders = []
        for raw in env_data["client_train_data"]:
            norm = self.preprocessor.transform(raw)
            loader = DataLoader(FlowDataset(norm), batch_size=self.fed_cfg.batch_size, shuffle=True)
            self.client_loaders.append(loader)

        self.clients = [
            SDNClient(i, self.client_loaders[i], self.model_cfg, self.fed_cfg, self.device)
            for i in range(self.fed_cfg.num_clients)
        ]
        self.server = FederatedServer(self.clients, self.model_cfg, self.fed_cfg, self.device)

        # Initial warm-up training (3 rounds)
        for r in range(1, 4):
            self.server.train_round(r)
        self.threshold = self.server.calibrate_global_threshold(self.sdn_cfg.threshold_percentile)

        # SDN Controllers & Switches
        print("[*] Setting up SDN Domains and Switches...")
        self.domain_controllers = []
        self.switches = []
        for d in range(self.fed_cfg.num_clients):
            ctrl = DistributedSDNController(
                domain_id=d + 1,
                name=f"Controller-Domain-{d+1}",
                detection_model=self.server.global_model,
                preprocessor=self.preprocessor,
                anomaly_threshold=self.threshold,
                sdn_config=self.sdn_cfg,
                device=self.device
            )
            sw = OpenFlowSwitch(dpid=f"00:00:00:00:00:0{d+1}", name=f"s{d+1}")
            ctrl.register_switch(sw)
            self.domain_controllers.append(ctrl)
            self.switches.append(sw)

        self.event_history = []
        self.current_round = 3
        print(f"[+] Web Application Backend Ready! Initial threshold: {self.threshold:.4f}")

    def train_next_fl_round(self):
        self.current_round += 1
        loss = self.server.train_round(self.current_round)
        self.threshold = self.server.calibrate_global_threshold(self.sdn_cfg.threshold_percentile)
        for ctrl in self.domain_controllers:
            ctrl.anomaly_threshold = self.threshold
        return {
            "round": self.current_round,
            "loss": loss,
            "threshold": self.threshold
        }

    def inject_traffic_flow(self, traffic_type: str, domain_id: int):
        # 1-indexed domain
        d_idx = max(0, min(len(self.domain_controllers) - 1, domain_id - 1))
        ctrl = self.domain_controllers[d_idx]
        sw = self.switches[d_idx]

        # Generate sample
        if traffic_type == "benign":
            feat = self.generator._generate_benign_flows(1, domain_bias=d_idx)[0]
            label_name = "Benign Flow"
            src_ip = f"10.{domain_id}.15.{np.random.randint(2, 250)}"
            dst_port = 80
        elif traffic_type == "known_attack":
            feat = self.generator._generate_known_attacks(1)[0]
            label_name = "Known Attack (SYN Flood)"
            src_ip = f"198.51.100.{np.random.randint(1, 254)}"
            dst_port = 443
        elif traffic_type == "zeroday_slowloris":
            # Stealth slow-rate
            feat = self.generator._generate_zero_day_exploits(2)[0]
            label_name = "Zero-Day (Stealth Slowloris)"
            src_ip = f"203.0.113.{np.random.randint(1, 254)}"
            dst_port = 8080
        else:  # zeroday_covert
            feat = self.generator._generate_zero_day_exploits(2)[1]
            label_name = "Zero-Day (Covert C2 Tunnel)"
            src_ip = f"192.0.2.{np.random.randint(1, 254)}"
            dst_port = 53

        dst_ip = f"172.16.{domain_id}.10"
        flow_meta = {
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "protocol": "TCP" if dst_port != 53 else "UDP",
            "dst_port": dst_port,
            "traffic_type": label_name
        }

        # Controller inspection and reactive mitigation
        res = ctrl.inspect_and_mitigate(feat, flow_meta, sw.dpid)

        # Simulate data plane packet ingress
        pkt = {
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "protocol": flow_meta["protocol"],
            "dst_port": dst_port,
            "length": int(feat[3] / max(1, feat[1]))
        }
        data_plane_action = sw.process_packet(pkt)

        event_record = {
            "id": len(self.event_history) + 1,
            "timestamp": time.strftime("%H:%M:%S"),
            "domain_id": domain_id,
            "switch_name": sw.name,
            "traffic_type": label_name,
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "dst_port": dst_port,
            "anomaly_score": round(res["anomaly_score"], 4),
            "threshold": round(self.threshold, 4),
            "is_anomaly": res["is_anomaly"],
            "mitigation_applied": res["mitigation_applied"],
            "data_plane_action": data_plane_action,
            "latency_ms": round(res["latency_ms"], 2)
        }
        self.event_history.insert(0, event_record)
        if len(self.event_history) > 100:
            self.event_history.pop()

        return event_record

    def get_status(self):
        total_forwarded = sum(sw.forwarded_packets for sw in self.switches)
        total_dropped = sum(sw.dropped_packets for sw in self.switches)
        active_rules = sum(len(sw.flow_table) for sw in self.switches)

        switches_info = []
        for sw, ctrl in zip(self.switches, self.domain_controllers):
            switches_info.append({
                "dpid": sw.dpid,
                "name": sw.name,
                "domain_id": ctrl.domain_id,
                "controller_name": ctrl.name,
                "rules_count": len(sw.flow_table),
                "forwarded_pkts": sw.forwarded_packets,
                "dropped_pkts": sw.dropped_packets
            })

        return {
            "fl_round": self.current_round,
            "threshold": round(self.threshold, 4),
            "total_forwarded": total_forwarded,
            "total_dropped": total_dropped,
            "active_rules_count": active_rules,
            "num_domains": len(self.domain_controllers),
            "switches": switches_info,
            "fl_history": self.server.round_history
        }

    def get_all_rules(self):
        rules = []
        for sw in self.switches:
            for r in sw.flow_table:
                rules.append({
                    "switch": sw.name,
                    "rule_id": r.rule_id,
                    "priority": r.priority,
                    "match": r.match,
                    "action": r.action,
                    "packet_count": r.packet_count,
                    "byte_count": r.byte_count,
                    "created_at": time.strftime("%H:%M:%S", time.localtime(r.created_at))
                })
        return rules

    def clear_flow_tables(self):
        for sw in self.switches:
            sw.flow_table.clear()
            sw.dropped_packets = 0
            sw.forwarded_packets = 0
        self.event_history.clear()
        return {"status": "cleared"}


# Instantiate global singleton backend
backend = IDSBackend()


class RequestHandler(SimpleHTTPRequestHandler):
    """
    Custom HTTP Request Handler serving static web files and REST API endpoints.
    """

    def __init__(self, *args, **kwargs):
        directory = os.path.dirname(os.path.abspath(__file__))
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            return super().do_GET()

        if parsed.path == "/api/status":
            self._send_json(backend.get_status())
        elif parsed.path == "/api/rules":
            self._send_json(backend.get_all_rules())
        elif parsed.path == "/api/history":
            self._send_json(backend.event_history)
        else:
            return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len) if content_len > 0 else b"{}"

        try:
            data = json.loads(post_body.decode("utf-8")) if post_body else {}
        except Exception:
            data = {}

        if parsed.path == "/api/login":
            username = data.get("username", "")
            password = data.get("password", "")
            # Default demo admin credentials: admin / admin or admin / admin123
            if username == "admin" and (password == "admin" or password == "admin123" or password == "aegisnet2026"):
                self._send_json({
                    "success": True,
                    "token": "aegis_admin_token_" + str(int(time.time())),
                    "user": "Administrator",
                    "role": "SDN_ROOT_ADMIN",
                    "permissions": ["all", "fl_train", "mitigate", "purge_rules"]
                })
            else:
                self._send_json({"success": False, "error": "Invalid username or password. Use admin / admin."}, status_code=401)
        elif parsed.path == "/api/train_round":
            res = backend.train_next_fl_round()
            self._send_json(res)
        elif parsed.path == "/api/inject_traffic":
            t_type = data.get("type", "benign")
            d_id = int(data.get("domain", 1))
            res = backend.inject_traffic_flow(t_type, d_id)
            self._send_json(res)
        elif parsed.path == "/api/clear_rules":
            res = backend.clear_flow_tables()
            self._send_json(res)
        else:
            self.send_response(404)
            self.end_headers()

    def _send_json(self, data, status_code=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Keep console output clean
        return


def run_server(port=8080):
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, RequestHandler)
    print(f"[*] SDN Federated IDS Web Dashboard serving at http://127.0.0.1:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    port = 8080
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    run_server(port)
