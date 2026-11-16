"""
Visualization Module for Federated Zero-Day Intrusion Detection.
Generates publication-quality charts for convergence, ROC curves, loss distributions, and confusion matrices.
"""

import os
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import roc_curve
from typing import List, Dict, Any
from config import OUTPUT_DIR


class PerformanceVisualizer:
    """
    Renders and saves experimental performance figures.
    """

    def __init__(self, output_dir: str = OUTPUT_DIR):
        self.output_dir = output_dir

    def plot_fl_convergence(self, round_history: List[Dict[str, Any]]):
        """
        Plots global model reconstruction loss across communication rounds.
        """
        rounds = [h["round"] for h in round_history]
        losses = [h["avg_client_loss"] for h in round_history]

        plt.figure(figsize=(8, 5))
        plt.plot(rounds, losses, marker="o", color="#1f77b4", linewidth=2.5, label="Global FL Loss")
        plt.title("Federated Learning Convergence Across SDN Domains", fontsize=13, fontweight="bold")
        plt.xlabel("Communication Round", fontsize=11)
        plt.ylabel("Mean Reconstruction Loss (Beta-VAE ELBO)", fontsize=11)
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend(fontsize=11)
        plt.tight_layout()

        path = os.path.join(self.output_dir, "fl_convergence.png")
        plt.savefig(path, dpi=300)
        plt.close()
        return path

    def plot_roc_curve(self, y_true: np.ndarray, anomaly_scores: np.ndarray, auc_score: float):
        """
        Plots Receiver Operating Characteristic (ROC) curve.
        """
        y_binary = (y_true > 0).astype(int)
        fpr, tpr, _ = roc_curve(y_binary, anomaly_scores)

        plt.figure(figsize=(7, 6))
        plt.plot(fpr, tpr, color="#d62728", lw=2.5, label=f"ROC Curve (AUC = {auc_score:.4f})")
        plt.plot([0, 1], [0, 1], color="#7f7f7f", linestyle="--", lw=1.5, label="Random Guess")
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel("False Positive Rate (FPR)", fontsize=11)
        plt.ylabel("True Positive Rate (Detection Rate)", fontsize=11)
        plt.title("Zero-Day & Anomaly Detection ROC Curve", fontsize=13, fontweight="bold")
        plt.legend(loc="lower right", fontsize=11)
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.tight_layout()

        path = os.path.join(self.output_dir, "roc_curve.png")
        plt.savefig(path, dpi=300)
        plt.close()
        return path

    def plot_score_distributions(
        self, y_true: np.ndarray, anomaly_scores: np.ndarray, threshold: float
    ):
        """
        Plots reconstruction loss distributions for Benign vs Known Attacks vs Zero-Day Exploits.
        """
        plt.figure(figsize=(10, 6))

        benign = anomaly_scores[y_true == 0]
        known = anomaly_scores[y_true == 1]
        zero_day = anomaly_scores[y_true == 2]

        bins = np.linspace(0, np.percentile(anomaly_scores, 99.5), 60)

        plt.hist(benign, bins=bins, alpha=0.6, color="#2ca02c", density=True, label="Benign Flows (Baseline)")
        plt.hist(known, bins=bins, alpha=0.5, color="#ff7f0e", density=True, label="Known Attacks (SYN Flood/Scan)")
        plt.hist(zero_day, bins=bins, alpha=0.6, color="#d62728", density=True, label="Zero-Day Exploits (Novel/Unseen)")

        plt.axvline(threshold, color="black", linestyle="--", linewidth=2.0, label=f"Anomaly Cutoff τ = {threshold:.3f}")

        plt.title("Reconstruction Anomaly Score Distribution Across Traffic Classes", fontsize=13, fontweight="bold")
        plt.xlabel("Reconstruction Error (MSE)", fontsize=11)
        plt.ylabel("Density", fontsize=11)
        plt.legend(fontsize=11)
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()

        path = os.path.join(self.output_dir, "anomaly_score_distribution.png")
        plt.savefig(path, dpi=300)
        plt.close()
        return path

    def plot_confusion_matrix(self, cm_dict: Dict[str, int]):
        """
        Renders binary confusion matrix table/heatmap.
        """
        matrix = np.array([
            [cm_dict["TN"], cm_dict["FP"]],
            [cm_dict["FN"], cm_dict["TP"]]
        ])

        plt.figure(figsize=(6, 5))
        plt.imshow(matrix, interpolation="nearest", cmap=plt.cm.Blues)
        plt.title("Intrusion Detection Confusion Matrix", fontsize=12, fontweight="bold")
        plt.colorbar()

        tick_marks = np.arange(2)
        plt.xticks(tick_marks, ["Benign (0)", "Attack (1/Zero-Day)"], fontsize=10)
        plt.yticks(tick_marks, ["Benign (0)", "Attack (1/Zero-Day)"], fontsize=10)

        thresh = matrix.max() / 2.0
        for i in range(2):
            for j in range(2):
                val = matrix[i, j]
                color = "white" if val > thresh else "black"
                plt.text(j, i, f"{val}\n({val / matrix.sum() * 100:.1f}%)",
                         horizontalalignment="center", verticalalignment="center",
                         color=color, fontsize=11, fontweight="bold")

        plt.ylabel("Ground Truth", fontsize=11)
        plt.xlabel("SDN Controller Decision", fontsize=11)
        plt.tight_layout()

        path = os.path.join(self.output_dir, "confusion_matrix.png")
        plt.savefig(path, dpi=300)
        plt.close()
        return path
