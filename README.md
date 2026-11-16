# Zero-Day Exploit Detection in Network Traffic via Federated Learning for Distributed Intrusion Detection in SDN Environments

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-orange.svg)](https://pytorch.org/)
[![OpenFlow 1.3](https://img.shields.io/badge/OpenFlow-1.3-green.svg)](https://opennetworking.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An end-to-end distributed network security framework combining **Federated Learning (FL)**, **Deep Variational Autoencoders (Beta-VAE)**, and **Software-Defined Networking (SDN)** to detect and mitigate zero-day exploits across multi-domain network topologies without sharing raw packet data.

---

## 🌟 Key Highlights

- **Unsupervised Zero-Day Detection**: Traditional signature-based IDSs fail against unobserved exploits. This system trains a **Beta-VAE** strictly on baseline benign network flows. When novel zero-day attacks or stealth exploits occur, their irregular topology triggers high reconstruction error.
- **Privacy-Preserving Federated Architecture**: Decentralized SDN controllers (e.g., Ryu, ONOS) train local models across heterogeneous domains (Enterprise, Cloud DC, IoT/Edge) using **FedProx** and **Local Differential Privacy (LDP)**.
- **Line-Rate SDN Reactive Mitigation**: Closed-loop control plane integration. When an anomaly is detected, the controller dynamically installs high-priority OpenFlow rules (`OFPFC_ADD`, `action=DROP` or `action=QUARANTINE`) into Data Plane OpenFlow switches (OVS) within milliseconds.
- **Zero Data Leakage**: Standard scaling and adaptive anomaly thresholding ($\tau$) are calculated strictly on normal baseline distributions.

---

## 🏗️ System Architecture

```
                    +------------------------------------+
                    |  Federated Aggregation Server      |
                    |  - FedAvg / FedProx Aggregator     |
                    |  - Differential Privacy LDP        |
                    +-----------------+------------------+
                                      | Global Weights W^(t)
          +---------------------------+---------------------------+
          |                           |                           |
+---------v-----------+     +---------v-----------+     +---------v-----------+
| SDN Domain 1 (LAN)  |     | SDN Domain 2 (DC)   |     | SDN Domain 3 (IoT)  |
| - Ryu/ONOS Sidecar  |     | - Ryu/ONOS Sidecar  |     | - Ryu/ONOS Sidecar  |
| - Local Beta-VAE    |     | - Local Beta-VAE    |     | - Local Beta-VAE    |
| - Feature Extractor |     | - Feature Extractor |     | - Feature Extractor |
+---------+-----------+     +---------+-----------+     +---------+-----------+
          | Telemetry                 | Telemetry                 | Telemetry
          | / FlowMod                 | / FlowMod                 | / FlowMod
+---------v-----------+     +---------v-----------+     +---------v-----------+
| OpenFlow Switch s1  |     | OpenFlow Switch s2  |     | OpenFlow Switch s3  |
| (OVS Data Plane)    |     | (OVS Data Plane)    |     | (OVS Data Plane)    |
+---------------------+     +---------------------+     +---------------------+
```

---

## 📁 Repository Structure

```
├── config.py                 # System hyperparameters (FL rounds, DP noise, SDN timeouts)
├── data/
│   ├── generator.py          # Synthetic InSDN/CIC-IDS flow generator (Benign, Known, Zero-Day)
│   ├── preprocessor.py       # Z-score normalization fitted strictly on baseline traffic
│   └── dataset.py            # PyTorch Dataset wrapper
├── models/
│   ├── autoencoder.py        # Deep Beta-VAE with reparameterization trick
│   └── loss.py               # Reconstruction MSE + Beta-weighted KL-Divergence ELBO
├── federated/
│   ├── client.py             # SDN Local Client with FedProx proximal regularization
│   ├── server.py             # Central Federated Aggregator
│   └── secure_agg.py         # L2 gradient clipping and Gaussian Differential Privacy
├── sdn/
│   ├── switch.py             # OpenFlow 1.3 vSwitch (OVS model, flow table matching)
│   ├── mitigation.py         # Reactive mitigation policy generator (OpenFlow FlowMod)
│   └── controller.py         # Distributed SDN Controller (Ryu / ONOS abstraction)
├── evaluation/
│   ├── metrics.py            # Comprehensive evaluation (Zero-day recall, ROC-AUC, FPR)
│   └── visualize.py          # Publication-ready plots (Convergence, ROC, Distributions)
├── tests/
│   └── test_pipeline.py      # Unit & integration test suite
├── output/                   # Generated charts, metrics JSON, and preprocessor state
└── run_simulation.py         # End-to-end execution script
```

---

## 🚀 Getting Started

### 1. Requirements
Ensure Python 3.9+ with PyTorch, Scikit-Learn, NumPy, and Matplotlib:
```bash
pip install torch numpy scikit-learn matplotlib joblib
```

### 2. Run Tests
```bash
python -m unittest discover tests
```

### 3. Run the Full Simulation
```bash
python run_simulation.py
```

The script will:
1. Generate multi-domain non-IID benign network flows, known attack flows, and novel zero-day attacks.
2. Partition data across 3 simulated SDN domains.
3. Perform 10 rounds of Federated Learning with FedProx.
4. Compute the adaptive anomaly threshold $\tau$.
5. Evaluate zero-day detection rate, ROC-AUC, and false positive rate.
6. Ingest live flow telemetry into SDN controllers and verify reactive `DROP` rule installation on OpenFlow switches.
7. Export metrics to `output/simulation_results.json` and generate publication charts in `output/`.

---

## 📊 Evaluation & Figures Generated

After running the simulation, the following figures are generated in `output/`:
- **`roc_curve.png`**: ROC Curve and Area Under Curve (AUC).
- **`fl_convergence.png`**: Multi-round Federated Learning convergence across domains.
- **`anomaly_score_distribution.png`**: Reconstruction loss distributions comparing Benign vs Known Attacks vs Zero-Day Novel Exploits, with decision threshold $\tau$.
- **`confusion_matrix.png`**: Normalized detection confusion matrix.

---

## 📄 Citation & Research Framework

If using this code or architecture for research papers, cite this framework as:
```bibtex
@article{federated_zeroday_sdn_2026,
  title={Zero-day Exploit Detection in Network Traffic via Federated Learning for Distributed Intrusion Detection in Software-Defined Networking Environments},
  author={Research Team},
  year={2026}
}
```
