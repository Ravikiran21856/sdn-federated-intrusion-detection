"""
Performance Evaluation Metrics for Zero-Day and Distributed Intrusion Detection.
"""

import numpy as np
from typing import Dict, Any, Tuple
from sklearn.metrics import roc_auc_score, roc_curve, precision_recall_fscore_support, confusion_matrix


class IDSEvaluator:
    """
    Computes rigorous intrusion detection metrics, with separate accounting
    for zero-day novel exploits vs known attack signatures.
    """

    @staticmethod
    def evaluate(
        y_true: np.ndarray,
        anomaly_scores: np.ndarray,
        threshold: float
    ) -> Dict[str, Any]:
        """
        y_true: 0 = Benign, 1 = Known Attack, 2 = Zero-Day Exploit
        anomaly_scores: continuous MSE reconstruction errors
        """
        # Binary prediction (0 = Normal, 1 = Attack)
        y_pred_binary = (anomaly_scores > threshold).astype(int)
        y_true_binary = (y_true > 0).astype(int)

        # Overall Binary Metrics
        p, r, f1, _ = precision_recall_fscore_support(
            y_true_binary, y_pred_binary, average="binary", zero_division=0
        )
        cm = confusion_matrix(y_true_binary, y_pred_binary)
        tn, fp, fn, tp = cm.ravel()
        fpr = fp / (fp + tn + 1e-9)

        # ROC-AUC
        auc = roc_auc_score(y_true_binary, anomaly_scores)

        # Sub-class Detection Rates
        known_mask = (y_true == 1)
        zero_day_mask = (y_true == 2)
        benign_mask = (y_true == 0)

        known_detection_rate = (
            np.mean(y_pred_binary[known_mask]) if np.any(known_mask) else 0.0
        )
        zero_day_detection_rate = (
            np.mean(y_pred_binary[zero_day_mask]) if np.any(zero_day_mask) else 0.0
        )
        benign_accuracy = (
            1.0 - np.mean(y_pred_binary[benign_mask]) if np.any(benign_mask) else 0.0
        )

        return {
            "roc_auc": float(auc),
            "precision": float(p),
            "recall": float(r),
            "f1_score": float(f1),
            "false_positive_rate": float(fpr),
            "benign_accuracy": float(benign_accuracy),
            "known_attack_detection_rate": float(known_detection_rate),
            "zero_day_detection_rate": float(zero_day_detection_rate),
            "confusion_matrix": {
                "TN": int(tn),
                "FP": int(fp),
                "FN": int(fn),
                "TP": int(tp)
            },
            "threshold_used": float(threshold)
        }
