"""
Complete End-to-End Simulation Runner:
Federated Learning for Zero-Day Exploit Detection and SDN Reactive Mitigation.
"""

import os
import json
import torch
import numpy as np
from torch.utils.data import DataLoader

from config import ModelConfig, FederatedConfig, SDNConfig, DataConfig, OUTPUT_DIR
from data.generator import SDNTrafficGenerator
from data.preprocessor import FlowDataPreprocessor
from data.dataset import FlowDataset
from federated.client import SDNClient
from federated.server import FederatedServer
from sdn.switch import OpenFlowSwitch
from sdn.controller import DistributedSDNController
from evaluation.metrics import IDSEvaluator
from evaluation.visualize import PerformanceVisualizer


def run_pipeline():
    print("=" * 80)
    print(" FEDERATED ZERO-DAY EXPLOIT DETECTION IN SDN ENVIRONMENTS ")
    print("=" * 80)

    # 1. Configuration & Reproducibility
    model_cfg = ModelConfig()
    fed_cfg = FederatedConfig()
    sdn_cfg = SDNConfig()
    data_cfg = DataConfig()

    torch.manual_seed(data_cfg.seed)
    np.random.seed(data_cfg.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[*] Compute Device: {device.upper()}")

    # 2. Data Generation & Domain Partitioning
    print("\n[Step 1/5] Generating Distributed SDN Telemetry (Non-IID Benign, Known Attacks, Zero-Day)...")
    generator = SDNTrafficGenerator(data_cfg)
    env_data = generator.generate_federated_environment()

    # Preprocessing
    preprocessor = FlowDataPreprocessor()
    # Fit scaler strictly on concatenated baseline benign training data (no leakage)
    all_train_benign = np.vstack(env_data["client_train_data"])
    preprocessor.fit(all_train_benign)
    preprocessor.save(os.path.join(OUTPUT_DIR, "preprocessor.joblib"))

    # Prepare Client DataLoaders
    client_loaders = []
    for i, client_raw in enumerate(env_data["client_train_data"]):
        norm_data = preprocessor.transform(client_raw)
        dataset = FlowDataset(norm_data)
        loader = DataLoader(dataset, batch_size=fed_cfg.batch_size, shuffle=True)
        client_loaders.append(loader)
        print(f"  -> SDN Domain {i+1} local dataset prepared: {len(norm_data)} benign baseline flows.")

    # Prepare Test Set
    test_norm = preprocessor.transform(env_data["test_features"])
    test_labels = env_data["test_labels"]
    test_tensor = torch.tensor(test_norm, dtype=torch.float32).to(device)

    # 3. Federated Learning Training
    print(f"\n[Step 2/5] Initializing Federated Clients & Aggregator ({fed_cfg.aggregation_method.upper()})...")
    clients = [
        SDNClient(
            client_id=i,
            dataloader=client_loaders[i],
            model_config=model_cfg,
            fed_config=fed_cfg,
            device=device
        )
        for i in range(fed_cfg.num_clients)
    ]

    server = FederatedServer(
        clients=clients,
        model_config=model_cfg,
        fed_config=fed_cfg,
        device=device
    )

    training_history = server.train()
    threshold = server.calibrate_global_threshold(percentile=sdn_cfg.threshold_percentile)
    print(f"\n[+] Federated Training Complete! Calibrated Anomaly Threshold (τ): {threshold:.4f}")

    # 4. Zero-Day Exploit Detection Evaluation
    print("\n[Step 3/5] Evaluating Zero-Day Detection on Unseen Network Flows...")
    global_model = server.global_model
    global_model.eval()
    with torch.no_grad():
        anomaly_scores = global_model.compute_anomaly_score(test_tensor).cpu().numpy()

    metrics = IDSEvaluator.evaluate(
        y_true=test_labels,
        anomaly_scores=anomaly_scores,
        threshold=threshold
    )

    print("\n" + "-" * 45)
    print(" DETECTION PERFORMANCE BENCHMARK ")
    print("-" * 45)
    print(f"  ROC-AUC Score                : {metrics['roc_auc'] * 100:.2f}%")
    print(f"  Overall Precision            : {metrics['precision'] * 100:.2f}%")
    print(f"  Overall Recall (All Attacks) : {metrics['recall'] * 100:.2f}%")
    print(f"  Overall F1-Score             : {metrics['f1_score'] * 100:.2f}%")
    print(f"  False Positive Rate (FPR)    : {metrics['false_positive_rate'] * 100:.2f}%")
    print(f"  Benign Traffic Accuracy      : {metrics['benign_accuracy'] * 100:.2f}%")
    print(f"  Known Attack Detection Rate  : {metrics['known_attack_detection_rate'] * 100:.2f}%")
    print(f"  >>> ZERO-DAY DETECTION RATE <<< : {metrics['zero_day_detection_rate'] * 100:.2f}%")
    print("-" * 45)

    # 5. SDN Control Plane Simulation & Reactive Mitigation
    print("\n[Step 4/5] Simulating SDN Control-Plane Telemetry & Reactive Flow Mitigation...")
    domain_controllers = []
    switches = []

    for d in range(fed_cfg.num_clients):
        ctrl = DistributedSDNController(
            domain_id=d + 1,
            name=f"Controller-Domain-{d+1}",
            detection_model=global_model,
            preprocessor=preprocessor,
            anomaly_threshold=threshold,
            sdn_config=sdn_cfg,
            device=device
        )
        sw = OpenFlowSwitch(dpid=f"00:00:00:00:00:0{d+1}", name=f"s{d+1}")
        ctrl.register_switch(sw)
        domain_controllers.append(ctrl)
        switches.append(sw)

    # Stream a subset of test flows through the SDN Controllers
    simulated_events = 200
    mitigated_count = 0
    total_latency_ms = 0.0

    for idx in range(simulated_events):
        feat = env_data["test_features"][idx]
        lbl = test_labels[idx]
        ctrl = domain_controllers[idx % len(domain_controllers)]
        sw = switches[idx % len(switches)]

        # Metadata for 5-tuple matching
        src_ip = f"10.{idx % 4}.{idx % 254}.{idx % 250 + 1}"
        dst_ip = "192.168.1.100"
        dst_port = 80 if lbl == 0 else (443 if lbl == 1 else 8080)
        flow_meta = {
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "protocol": "TCP",
            "dst_port": dst_port,
            "ground_truth_label": int(lbl)
        }

        res = ctrl.inspect_and_mitigate(feat, flow_meta, sw.dpid)
        total_latency_ms += res["latency_ms"]
        if res["mitigation_applied"]:
            mitigated_count += 1
            # Verify data plane packet enforcement
            pkt = {"src_ip": src_ip, "dst_ip": dst_ip, "protocol": "TCP", "dst_port": dst_port, "length": 512}
            action_taken = sw.process_packet(pkt)
            assert action_taken == "DROP", f"Rule enforcement failed: expected DROP, got {action_taken}"

    avg_mitigation_latency = total_latency_ms / simulated_events
    print(f"  [+] Ingested {simulated_events} live telemetry flows across {len(domain_controllers)} SDN controllers.")
    print(f"  [+] Anomalous / Zero-Day Flows Mitigated : {mitigated_count}")
    print(f"  [+] Average Control-Plane Defense Latency: {avg_mitigation_latency:.2f} ms")
    print(f"  [+] Data Plane Policy Enforcement        : 100% verified (OVS flow table DROP active)")

    # 6. Publication Visualizations
    print("\n[Step 5/5] Generating Visualizations and Exporting Metrics...")
    visualizer = PerformanceVisualizer(OUTPUT_DIR)
    conv_fig = visualizer.plot_fl_convergence(training_history)
    roc_fig = visualizer.plot_roc_curve(test_labels, anomaly_scores, metrics["roc_auc"])
    dist_fig = visualizer.plot_score_distributions(test_labels, anomaly_scores, threshold)
    cm_fig = visualizer.plot_confusion_matrix(metrics["confusion_matrix"])

    # Export results JSON
    results_path = os.path.join(OUTPUT_DIR, "simulation_results.json")
    with open(results_path, "w") as f:
        json.dump({
            "metrics": metrics,
            "avg_mitigation_latency_ms": avg_mitigation_latency,
            "mitigated_events": mitigated_count,
            "simulated_events": simulated_events,
            "figures": {
                "convergence": conv_fig,
                "roc_curve": roc_fig,
                "score_distribution": dist_fig,
                "confusion_matrix": cm_fig
            }
        }, f, indent=4)

    print(f"\n[SUCCESS] Pipeline executed successfully!")
    print(f"  -> Metrics JSON saved: {results_path}")
    print(f"  -> Generated Figures saved in: {OUTPUT_DIR}")


if __name__ == "__main__":
    run_pipeline()
