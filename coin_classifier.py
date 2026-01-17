import os
import torch
import torchvision
import torchvision.transforms as transforms
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm
from PIL import Image
import torch.nn as nn
import torch.optim as optim
import torchvision.models as models
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix, roc_curve, auc
from sklearn.preprocessing import label_binarize
import matplotlib.pyplot as plt
import cv2

class Config:
    def __init__(self):
        # Using the exact paths from your code
        self.base_dir = r"C:\Users\Oindrieel\Desktop\IEDC\website\ai_model\Dataset"

        self.train_dir = os.path.join(self.base_dir, "train")
        self.val_dir   = os.path.join(self.base_dir, "val")
        self.test_dir  = os.path.join(self.base_dir, "test")

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.input_channels = 4
        self.num_prototypes_per_class = 10

        self.batch_size = 32
        self.epochs = 25
        self.freeze_epochs = 5

        self.lr_features = 1e-4
        self.lr_prototypes = 3e-4
        self.lr_last_layer = 1e-3

        self.image_size = 256

        self.save_dir = r"C:\Users\Oindrieel\Desktop\IEDC\website\ai_model\Save"
        os.makedirs(self.save_dir, exist_ok=True)
        self.save_path = os.path.join(self.save_dir, "model.pth")

        # 🔹 NEW: preload switch
        self.preload_data = False


# ============================================================
# DATASET
# ============================================================
class ProtoFeatureDataset(Dataset):
    def __init__(self, root_dir, preload=False):
        self.root_dir = root_dir
        self.preload = preload
        self.samples = []
        self.preloaded_data = None

        if os.path.exists(root_dir):
            self.classes = sorted(
                d for d in os.listdir(root_dir)
                if os.path.isdir(os.path.join(root_dir, d))
            )
            self.class_to_idx = {c: i for i, c in enumerate(self.classes)}

            for cls in self.classes:
                cls_dir = os.path.join(root_dir, cls)
                for f in os.listdir(cls_dir):
                    if f.endswith(".pt"):
                        self.samples.append(
                            (os.path.join(cls_dir, f), self.class_to_idx[cls])
                        )
        else:
            self.classes = []
            self.class_to_idx = {}

        if self.preload:
            self.preload_from_disk()

    def preload_from_disk(self):
        print(f"Preloading {len(self.samples)} samples from {self.root_dir}")
        self.preloaded_data = []
        for path, label in tqdm(self.samples):
            x = torch.load(path).float()
            self.preloaded_data.append((x, label))

    def __len__(self):
        return len(self.preloaded_data) if self.preloaded_data else len(self.samples)

    def __getitem__(self, idx):
        if self.preloaded_data:
            return self.preloaded_data[idx]
        path, label = self.samples[idx]
        return torch.load(path).float(), label


# ============================================================
# BACKBONE
# ============================================================
class DenseNetBackbone(nn.Module):
    def __init__(self, in_channels=4, out_dim=128):
        super().__init__()

        net = models.densenet121(weights=models.DenseNet121_Weights.IMAGENET1K_V1)

        old_conv = net.features.conv0
        new_conv = nn.Conv2d(
            in_channels,
            old_conv.out_channels,
            kernel_size=old_conv.kernel_size,
            stride=old_conv.stride,
            padding=old_conv.padding,
            bias=False,
        )

        with torch.no_grad():
            new_conv.weight[:, :3] = old_conv.weight
            # Handle the extra channel initialization
            new_conv.weight[:, 3:] = old_conv.weight.mean(dim=1, keepdim=True)

        net.features.conv0 = new_conv

        self.encoder = net.features
        self.pool = nn.AdaptiveAvgPool2d((4, 4))
        self.project = nn.Conv2d(1024, out_dim, 1)

    def forward(self, x):
        x = self.encoder(x)
        x = self.pool(x)
        return self.project(x)


# ============================================================
# PROTOPNET
# ============================================================
class ProtoPNet(nn.Module):
    def __init__(self, cfg, num_classes):
        super().__init__()

        self.k = cfg.num_prototypes_per_class
        self.P = num_classes * self.k

        self.features = DenseNetBackbone(cfg.input_channels)
        self.add_on = nn.ReLU()

        self.prototype_vectors = nn.Parameter(torch.randn(self.P, 128))
        self.last_layer = nn.Linear(self.P, num_classes, bias=False)

        self._init_last_layer()

    def _init_last_layer(self):
        self.last_layer.weight.data.zero_()
        for j in range(self.P):
            self.last_layer.weight.data[j // self.k, j] = 1.0

    def forward(self, x):
        x = self.add_on(self.features(x))
        B, C, H, W = x.shape
        x = x.view(B, C, -1).permute(0, 2, 1)

        x2 = (x ** 2).sum(dim=2, keepdim=True)
        p2 = (self.prototype_vectors ** 2).sum(dim=1)
        xp = torch.matmul(x, self.prototype_vectors.t())

        distances = x2 - 2 * xp + p2.view(1, 1, -1)
        distances = distances.min(dim=1)[0]

        logits = self.last_layer(-distances)
        return logits, distances