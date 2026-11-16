"""
Data Preprocessor and Scaler for Network Telemetry Features.
Ensures zero data leakage: fitted strictly on baseline training flows.
"""

import numpy as np
import joblib
import os
from typing import Tuple, List
from config import OUTPUT_DIR


class FlowDataPreprocessor:
    """
    Fits standard scaling on normal baseline flows and transforms both
    local client datasets and test evaluation flows.
    """

    def __init__(self):
        self.mean_ = None
        self.scale_ = None

    def fit(self, normal_flows: np.ndarray):
        """
        Calculates mean and standard deviation from benign training traffic.
        """
        self.mean_ = np.mean(normal_flows, axis=0)
        self.scale_ = np.std(normal_flows, axis=0)
        # Avoid division by zero on static features (e.g. constant headers)
        self.scale_[self.scale_ < 1e-6] = 1.0

    def transform(self, flows: np.ndarray) -> np.ndarray:
        """
        Applies standard z-score normalization: (x - mean) / scale.
        """
        if self.mean_ is None or self.scale_ is None:
            raise ValueError("Preprocessor has not been fitted yet!")
        return (flows - self.mean_) / self.scale_

    def fit_transform(self, normal_flows: np.ndarray) -> np.ndarray:
        self.fit(normal_flows)
        return self.transform(normal_flows)

    def save(self, filepath: str = os.path.join(OUTPUT_DIR, "preprocessor.joblib")):
        joblib.dump({"mean": self.mean_, "scale": self.scale_}, filepath)

    def load(self, filepath: str = os.path.join(OUTPUT_DIR, "preprocessor.joblib")):
        data = joblib.load(filepath)
        self.mean_ = data["mean"]
        self.scale_ = data["scale"]
