# COLLEGE DEFENSE PRESENTATION SLIDES & SPEAKER NOTES

**Project Title:** Zero-Day Exploit Detection in Network Traffic via Federated Learning for Distributed Intrusion Detection in Software-Defined Networking (SDN) Environments  
**System Name:** AEGISNET  
**Candidate Name:** RAVI KIRAN  
**Department:** Computer Science & Engineering / Information Security  
**Academic Year:** 2025 – 2026  

---

## SLIDE 1: TITLE SLIDE
* **Title:** Zero-Day Exploit Detection in Network Traffic via Federated Learning for Distributed Intrusion Detection in SDN Environments
* **Framework:** AEGISNET Cyber Defense Platform
* **Candidate:** NVV RAVI KIRAN (Roll No: **24ME5A4605**)
* **Guide / Supervisor:** Ms. G. VISHNU PRIYANKA, Assistant Professor, Dept. of CSE (Cyber Security)
* **Head of Department:** Dr. B. NARENDRA, HoD (CSE - Cyber Security)
* **Institutional Details:** Ramachandra College of Engineering (Autonomous), Eluru, A.P. (Academic Year 2026–2027)

> **🎤 Speaker Notes:**  
> "Good morning, respected members of the evaluation committee and my project guide. Today, I am presenting our major project titled *Zero-Day Exploit Detection in Network Traffic via Federated Learning for Distributed Intrusion Detection in Software-Defined Networking Environments*. In this project, we have designed and implemented an end-to-end framework, called AEGISNET, that detects novel, unobserved zero-day cyber exploits without sharing raw private packet telemetry, while enforcing line-rate mitigation using OpenFlow 1.3 switches in less than half a millisecond."

---

## SLIDE 2: PROBLEM STATEMENT & MOTIVATION
* **The Zero-Day Vulnerability Crisis:**
  * Cyber adversaries exploit unknown software flaws before patches or signatures exist.
  * Signature engines (Snort/Suricata) have **0% detection** on day zero.
* **The Privacy & Regulatory Dilemma:**
  * Privacy laws (GDPR, HIPAA, CCPA) strictly prohibit pooling raw packet telemetry across institutions or enterprise domains into a central server.
* **The Bandwidth & Controller Bottleneck:**
  * Centralizing high-throughput multi-gigabit traffic across WAN links causes severe bandwidth exhaustion and controller saturation.

> **🎤 Speaker Notes:**  
> "To understand the urgency of this work, consider the problem statement. Traditional security systems fail against zero-day exploits because they look for known signatures. If a signature hasn't been written, the attack passes undetected. Secondly, modern enterprise networks cannot legally or practically pool sensitive network flows into a single central data center due to strict privacy regulations like GDPR. Finally, centralized analysis creates major bandwidth chokes and single points of failure. Our goal is to solve all three issues simultaneously."

---

## SLIDE 3: EXISTING APPROACHES VS. LIMITATIONS
* **Signature-Based Systems (Snort, Suricata):**
  * Fast on known attacks, but completely blind to zero-day variations and polymorphic threats.
* **Supervised Machine Learning (Random Forests, SVM, DNN):**
  * Requires extensive labeled attack datasets; suffers from severe distribution shift and misclassifies novel attacks as benign.
* **Centralized Data Lakes:**
  * High communication latency, privacy violations, and vulnerability to centralized exfiltration.
* **Standard Federated Learning (FedAvg):**
  * Fails to converge stably when network traffic across domains is Non-IID (heterogeneous).

> **🎤 Speaker Notes:**  
> "When we reviewed existing solutions, we observed critical limitations. Supervised classifiers fail because they assume test traffic will look like training traffic. Standard Federated Averaging (FedAvg) assumes all networks have the same traffic distribution, which fails completely when combining IoT, enterprise, and cloud data centers. This highlighted the need for an unsupervised generative approach paired with a heterogeneity-tolerant federated algorithm."

---

## SLIDE 4: PROPOSED SOLUTION - AEGISNET
* **Unsupervised Latent Representation:**
  * Employs a **Deep Beta-Variational Autoencoder ($\beta$-VAE)** trained strictly on legitimate baseline traffic.
* **Privacy-Preserving Federated Aggregation:**
  * Employs **FedProx** with proximal regularization ($\mu = 0.01$) to handle non-IID domain distributions.
  * Guarantees **Local Differential Privacy (LDP)** via gradient clipping and calibrated Gaussian perturbation.
* **Line-Rate SDN Reactive Defense:**
  * Closed-loop **OpenFlow 1.3** integration installs hardware-level `DROP` rules (`priority=65535`) directly into Open vSwitch (OVS) within **$0.49\text{ ms}$**.
* **Interactive Operations Dashboard:**
  * Real-time 1-second glassmorphic console for operational telemetry and manual exploit testing.

> **🎤 Speaker Notes:**  
> "Our proposed system, AEGISNET, introduces three primary innovations. First, instead of training on attacks, we train an unsupervised $\beta$-VAE strictly on normal baseline traffic. Second, we use FedProx with Differential Privacy so multiple network domains can collaboratively learn a global detection baseline without ever exposing their raw packets. Third, the moment an anomaly is detected, the SDN controller writes high-priority drop rules directly into switch hardware in 0.49 milliseconds, isolating the attacker at line rate."

---

## SLIDE 5: SYSTEM ARCHITECTURE & TOPOLOGY
* **Tier 1 - Central Federated Aggregator:**
  * Coordinates training rounds, aggregates model parameters, and enforces Differential Privacy.
* **Tier 2 - Distributed SDN Controllers (Ryu/ONOS):**
  * Domain 1: Enterprise Campus (s1)
  * Domain 2: Cloud Data Center (s2)
  * Domain 3: IoT / Edge Subnet (s3)
* **Tier 3 - SDN Data Plane (Open vSwitch):**
  * Processes packets at wire speed, executes FlowMod commands, and tracks hardware telemetry counters.

> **🎤 Speaker Notes:**  
> "This slide illustrates the three-tier architecture of AEGISNET. At Tier 1, the central federated coordinator orchestrates learning rounds without seeing any flow data. Tier 2 contains local SDN controllers in three distinct network domains: Enterprise, Cloud, and IoT. Tier 3 consists of OpenFlow switches that forward packets at wire speed and immediately drop malicious flows once a rule is installed."

---

## SLIDE 6: MATHEMATICAL FORMULATION - DEEP $\beta$-VAE
* **Generative Probabilistic Modeling:**
  * Encoder $q_\phi(z|x)$ maps 16-D flow features $x$ into an 8-D Gaussian latent distribution $\mathcal{N}(\mu_z, \sigma_z^2)$.
  * Decoder $p_\theta(x|z)$ reconstructs the flow vector $\hat{x}$.
* **The Reparameterization Trick:**
  $$z = \mu_z(x) + \sigma_z(x) \odot \epsilon, \quad \epsilon \sim \mathcal{N}(0, I)$$
* **$\beta$-VAE Loss Function (ELBO):**
  $$\mathcal{L}_{\beta\text{-VAE}} = \mathbb{E}_{q_\phi(z|x)}\left[\|x - \hat{x}\|^2\right] + \beta \cdot D_{\text{KL}}\left(q_\phi(z|x) \parallel \mathcal{N}(0, I)\right)$$
* **Role of $\beta = 1.25$:**
  * Enforces an information bottleneck that disentangles latent features and prevents memorization of anomalous noise.

> **🎤 Speaker Notes:**  
> "Mathematically, the core of our detector is the $\beta$-Variational Autoencoder. The encoder compresses a 16-dimensional flow vector into an 8-dimensional latent space. By using the reparameterization trick, the network remains fully differentiable. The parameter beta equals 1.25, which balances reconstruction accuracy against latent space regularization, ensuring the model generalizes well to normal traffic while remaining sensitive to anomalies."

---

## SLIDE 7: ZERO-DAY ANOMALY SCORING & ADAPTIVE THRESHOLD $\tau$
* **Anomaly Metric (Reconstruction MSE):**
  $$S(x) = \frac{1}{D} \sum_{j=1}^D (x_j - \hat{x}_j)^2$$
* **Mathematical Detection Mechanism:**
  * **Normal Flows:** Model reconstructs accurately $\implies S(x) \le 1.0$ (Low Error).
  * **Novel Zero-Day Exploits:** Contain unobserved structural patterns $\implies S(x) \gg 1.93$ (High Error).
* **Strict Anti-Data Leakage Threshold Selection:**
  $$\tau = \mu_{\text{benign\_val}} + 3.0 \cdot \sigma_{\text{benign\_val}} = 1.9325$$
  * Established strictly on normal validation traffic (three-sigma boundary). Zero attack data used to set $\tau$.

> **🎤 Speaker Notes:**  
> "How does AEGISNET detect zero-day exploits without seeing them beforehand? It measures reconstruction error. Because the network only learns the structure of benign traffic, it easily reconstructs normal flows. But when a zero-day exploit arrives—such as a stealth Slowloris or a DNS tunnel—the model cannot reconstruct it, resulting in a spike in error. We set our threshold tau at 1.9325 using a strict three-sigma rule on validation baseline data, ensuring zero data leakage."

---

## SLIDE 8: FEDERATED OPTIMIZATION VIA FEDPROX
* **Overcoming Non-IID Statistical Heterogeneity:**
  * In standard FedAvg, divergent local client models cause global aggregation to diverge.
* **FedProx Local Regularized Objective:**
  $$\min_w h_k(w; w^t) = F_k(w) + \frac{\mu}{2} \|w - w^t\|^2$$
  * $\mu = 0.01$ restricts local models from straying too far from the global consensus $w^t$.
* **Differential Privacy Guarantee:**
  * $\ell_2$-gradient clipping: $C = 1.0$
  * Calibrated Gaussian noise: $\sigma_{\text{DP}} = 0.001$
  * Satisfies $(\epsilon, \delta)$-Differential Privacy ($\epsilon \le 4.0$).

> **🎤 Speaker Notes:**  
> "To train across heterogeneous domains, we implemented FedProx instead of standard FedAvg. Network traffic in an IoT subnet is fundamentally different from a cloud data center. FedProx adds a proximal regularization term with mu = 0.01 that mathematically prevents local client drift. Furthermore, by applying L2-norm clipping and Gaussian noise, we guarantee Differential Privacy against gradient inversion attacks."

---

## SLIDE 9: CLOSED-LOOP SDN REACTIVE MITIGATION
* **OpenFlow 1.3 Protocol FlowMod:**
  * Match Condition: `ipv4_src`, `ipv4_dst`, `protocol`, `dst_port`
  * Action: `OFPAT_DROP`
  * Priority: `65535` (Maximum Priority)
  * Timeouts: `idle_timeout = 300s`, `hard_timeout = 600s`
* **Sub-Millisecond Execution:**
  * Average mitigation latency: **$0.49\text{ ms}$**
* **Hardware Offloading:**
  * Once installed in Table 0, all matching attack packets are dropped directly in switch hardware at wire speed with **zero controller interaction**.

> **🎤 Speaker Notes:**  
> "A key contribution of our system is closed-loop integration with SDN. Detection alone is not enough; the attack must be stopped instantly. The controller generates an OpenFlow 1.3 FlowMod rule with maximum priority 65535 and action DROP. This takes only 0.49 milliseconds. Once installed on the Open vSwitch, subsequent attack packets are dropped in hardware at wire speed, completely shielding the controller."

---

## SLIDE 10: 16-DIMENSIONAL SDN FLOW FEATURE SPACE
* **Flow Duration & Volume:** `duration`, `packet_count`, `byte_count`
* **Packet Size Dynamics:** `pkt_len_mean`, `pkt_len_std`, `pkt_len_min`, `pkt_len_max`
* **Transmission Rates:** `flow_pkt_rate`, `flow_byte_rate`
* **TCP Flag Distribution:** `syn_count`, `ack_count`, `fin_count`, `rst_count`, `psh_count`, `urg_count`
* **Transport Protocol:** `protocol_num` (6 for TCP, 17 for UDP)

> **🎤 Speaker Notes:**  
> "Here we see our 16-dimensional flow feature vector. We extract flow duration, packet counts, byte statistics, rate metrics, and individual TCP flags. These 16 features capture both volumetric anomalies like SYN floods and low-rate stealth anomalies like Slowloris attacks."

---

## SLIDE 11: EXPERIMENTAL SETUP & ATTACK SCENARIOS
* **Evaluation Dataset:** 2,000 multi-domain flows (1,000 Benign, 500 Known Attacks, 500 Zero-Day Exploits).
* **Domain 1 (Enterprise LAN):** Known SYN Flood DoS.
* **Domain 2 (Cloud Data Center):** Novel Zero-Day Stealth Slowloris (ultra-low packet rate, elongated TCP connections).
* **Domain 3 (Edge / IoT Subnet):** Novel Zero-Day Covert C2 DNS Tunneling (atypical payload lengths over UDP port 53).

> **🎤 Speaker Notes:**  
> "For our evaluation, we simulated three heterogeneous domains. Domain 1 represents an Enterprise LAN subjected to SYN floods. Domain 2 simulates a Cloud Data Center attacked by a novel stealth Slowloris zero-day exploit. Domain 3 represents an Edge IoT network attacked by a covert DNS tunneling exploit. These zero-day exploits were never seen by the model during training."

---

## SLIDE 12: RESULTS - ROC-AUC PERFORMANCE (98.46%)
* **Receiver Operating Characteristic (ROC):**
  * **Measured ROC-AUC:** **$98.46\%$**
* **Operational Implication:**
  * Proves near-optimal separability between legitimate traffic and attacks.
  * Demonstrates that the unsupervised $\beta$-VAE latent boundary accurately discriminates anomalous flows without labeled attack supervision.

> **🎤 Speaker Notes:**  
> "This slide presents our ROC curve. AEGISNET achieved an exceptional ROC-AUC of 98.46%. In binary classification, an AUC above 98% indicates near-flawless discriminatory power. This confirms that reconstruction error in our beta-VAE latent space effectively separates benign flows from malicious attacks."

---

## SLIDE 13: RESULTS - ZERO-DAY VS. KNOWN ATTACK RECALL
* **Known Attack Detection Rate:** **$100.00\%$** (500 / 500 intercepted)
* **Zero-Day Exploit Detection Rate:** **$79.20\%$** (396 / 500 intercepted)
* **Benchmark Comparison:**
  * Signature engines (Snort/Suricata): **$0\%$** Zero-Day Detection
  * Supervised ML (Random Forest): **$14.2\%$** Zero-Day Detection
  * **AEGISNET (Proposed):** **$79.2\%$ Zero-Day Detection**

> **🎤 Speaker Notes:**  
> "This is the most critical result of our dissertation. On known signature attacks, our model achieved a 100% detection rate. On completely unseen, novel zero-day exploits, AEGISNET successfully detected and mitigated 79.20% of attacks on day zero. In comparison, traditional signature systems achieve zero percent detection because no signatures exist."

---

## SLIDE 14: RESULTS - CONFUSION MATRIX & CLASSIFICATION METRICS
* **Overall Precision:** **$94.22\%$** (Low false alarm fatigue)
* **Overall Recall:** **$89.60\%$** (High sensitivity across all attacks)
* **Overall F1-Score:** **$91.85\%$**
* **False Positive Rate (FPR):** **$5.50\%$**
* **Confusion Matrix Breakdown (2,000 samples):**
  * True Negatives (TN): **$945$**
  * True Positives (TP): **$896$**
  * False Positives (FP): **$55$**
  * False Negatives (FN): **$104$**

> **🎤 Speaker Notes:**  
> "Looking at the overall classification metrics across all 2,000 test flows: our precision is 94.22%, recall is 89.60%, and F1-score is 91.85%. Out of 1,000 benign flows, 945 were correctly allowed without disruption, resulting in a false positive rate of only 5.5%, which is well within acceptable limits for enterprise networks."

---

## SLIDE 15: RESULTS - FEDERATED CONVERGENCE & PRIVACY
* **Monotonic Loss Reduction across 10 FedProx Rounds:**
  * Round 1: Loss = $1.4120$
  * Round 3: Loss = $0.9845$
  * Round 6: Loss = $0.7210$
  * Round 10: Loss = $0.5621$
* **No Divergence or Oscillation:** Proximal term $\mu = 0.01$ stabilized aggregation across non-IID domains.
* **Privacy Verification:** Zero raw packets transmitted across network boundaries.

> **🎤 Speaker Notes:**  
> "Here we observe the federated learning convergence curve across 10 communication rounds. Global reconstruction loss drops smoothly from 1.41 down to 0.56 without any divergence or oscillations. The proximal parameter mu ensured that each domain's local model converged toward a shared consensus while keeping all raw telemetry on-premise."

---

## SLIDE 16: RESULTS - SUB-MILLISECOND MITIGATION LATENCY
* **Latency Component Breakdown:**
  * Feature Extraction: $0.12\text{ ms}$
  * $\beta$-VAE Neural Inference: $0.28\text{ ms}$
  * OpenFlow 1.3 FlowMod Generation & Push: $0.09\text{ ms}$
* **Total Defense Latency:** **$0.49\text{ ms}$** ($< 0.5\text{ ms}$)
* **Impact:** Neutralizes attacks before buffer exhaustion or controller saturation can occur.

> **🎤 Speaker Notes:**  
> "This slide breaks down our control plane mitigation latency. Feature extraction takes 0.12 milliseconds, PyTorch VAE inference takes 0.28 milliseconds, and OpenFlow rule generation takes 0.09 milliseconds. Total mitigation latency is just 0.49 milliseconds. Sub-millisecond defense guarantees that attacks are stopped before high-rate traffic can impact network availability."

---

## SLIDE 17: LIVE CYBER OPERATIONS DASHBOARD (AEGISNET)
* **Glassmorphic Cyber HUD Console:**
  * Real-time 1-second telemetry stream and heartbeat counter.
  * Dynamic VAE loss curve with live MSE readout, threat level bar, and threshold line.
  * Active OpenFlow 1.3 flow table with live incrementing packet drop counters (`+X/s`) and TTL expiry.
  * Animated SVG topology demonstrating physical SDN packet interception at the switch level.
  * Role-Based Access Control (Admin Login: `admin / admin`).

> **🎤 Speaker Notes:**  
> "To provide complete situational awareness, we developed the AEGISNET Cyber Operations Dashboard. The dashboard streams telemetry updates every second, tracks real-time VAE reconstruction loss, displays active OpenFlow rules with live incrementing counters, and features an interactive SVG topology showing packets being dropped at the switch. We also implemented RBAC admin authentication to safeguard manual attack injection."

---

## SLIDE 18: COMPARATIVE ANALYSIS WITH BASELINES
* **Snort / Suricata:** Centralized, 0% Zero-Day Recall, No reactive mitigation.
* **Centralized Random Forest:** Centralized, 14.2% Zero-Day Recall, 84.1% AUC, No reactive mitigation.
* **Isolation Forest:** Centralized, 58.4% Zero-Day Recall, 88.7% AUC, No reactive mitigation.
* **Standard FedAvg + MLP:** Federated, 18.5% Zero-Day Recall, 81.2% AUC, No reactive mitigation.
* **AEGISNET (Proposed):** **Federated (LDP), 79.2% Zero-Day Recall, 98.46% AUC, 0.49 ms OpenFlow Mitigation.**

> **🎤 Speaker Notes:**  
> "When comparing AEGISNET against standard benchmarks: traditional tools like Snort achieve 0% zero-day recall. Supervised models like Random Forest achieve only 14.2% recall on novel attacks. Unsupervised Isolation Forest reaches 58.4%. AEGISNET outperforms all of them with 79.2% zero-day detection and 98.46% ROC-AUC, while being the only system that provides privacy-preserving federated training and automated 0.49 ms OpenFlow mitigation."

---

## SLIDE 19: CONCLUSIONS & CONTRIBUTIONS
* **Summary of Achievements:**
  1. Developed unsupervised Deep $\beta$-VAE achieving **$98.46\%$ ROC-AUC** and **$79.2\%$ Zero-Day Recall**.
  2. Solved multi-domain statistical heterogeneity via **FedProx ($\mu = 0.01$)** with Differential Privacy.
  3. Deployed sub-millisecond (**$0.49\text{ ms}$**) OpenFlow 1.3 reactive mitigation.
  4. Built and deployed a live interactive glassmorphic cyber defense dashboard.
* **Current Limitations:**
  * Ultra-low-rate single-packet anomalies require multi-packet flow aggregation windows.

> **🎤 Speaker Notes:**  
> "In conclusion, AEGISNET successfully demonstrates that combining unsupervised generative models with federated learning and Software-Defined Networking provides a practical, scalable, and privacy-preserving defense against zero-day threats. We achieved a 98.46% ROC-AUC, detected nearly 80% of novel zero-day attacks, and mitigated threats in under 0.5 milliseconds."

---

## SLIDE 20: FUTURE SCOPE & THANK YOU
* **Future Research Directions:**
  * Integration of **Graph Neural Networks (GNNs)** for inter-switch topological path correlation.
  * Hardware acceleration on programmable **P4 ASICs** for sub-microsecond in-switch inference.
  * Defensive distillation against adversarial autoencoder evasion attacks.
* **Project Artifacts:**
  * GitHub Repository: [https://github.com/Ravikiran21856/sdn-federated-intrusion-detection](https://github.com/Ravikiran21856/sdn-federated-intrusion-detection)
  * Live Web Demo: [https://ravikiran21856.github.io/sdn-federated-intrusion-detection/](https://ravikiran21856.github.io/sdn-federated-intrusion-detection/)
* **Thank you! Questions and Discussion.**

> **🎤 Speaker Notes:**  
> "Looking ahead, we plan to explore Graph Neural Networks for cross-path topology analysis and compile the model into P4 programmable ASICs for hardware-level sub-microsecond inference. Our entire project, automated test suite, live dashboard, and documentation are available on GitHub. Thank you for your time, and I am now ready to take your questions."
