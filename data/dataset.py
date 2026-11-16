"""
PyTorch Dataset Definition for Network Flow Telemetry.
"""

import torch
from torch.utils.data import Dataset
import numpy as np


class FlowDataset(Dataset):
    """
    Wraps preprocessed SDN flow feature vectors for PyTorch DataLoader.
    """

    def __init__(self, features: np.ndarray, labels: np.ndarray = None):
        self.features = torch.tensor(features, dtype=torch.float32)
        if labels is not None:
            self.labels = torch.tensor(labels, dtype=torch.long)
        else:
            self.labels = None

    def __len__(self) -> int:
        return len(self.features)

    def __getitem__(self, idx: int):
        if self.labels is not None:
            return self.features[idx], self.labels[idx]
        return self.features[idx]
