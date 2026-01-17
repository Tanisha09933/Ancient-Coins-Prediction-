import torch
import torchvision.transforms as transforms
from PIL import Image
from io import BytesIO
import os

# Import the classes from your coin_classifier file
from .coin_classifier import Config, ProtoPNet


class Predictor:
    def __init__(self):
        """
        Initializes the predictor with the new ProtoPNet model.
        """
        self.config = Config()
        # Force CPU for web server inference to ensure stability
        self.config.device = "cpu"

        print(f"[AI Predictor] Loading ProtoPNet (DenseNet) model from: {self.config.save_path}")

        # 1. Load classes to determine num_classes (needed for model init)
        self.classes, self.idx_to_class = self._load_classes()
        num_classes = len(self.classes)

        if num_classes == 0:
            print("[AI Predictor] Warning: No classes found. Using default 39 to avoid crash.")
            num_classes = 39

            # 2. Initialize the model structure with correct num_classes
        self.model = ProtoPNet(self.config, num_classes).to(self.config.device)

        # 3. Load the trained weights
        if os.path.exists(self.config.save_path):
            try:
                # map_location is crucial when loading models on a CPU machine
                state_dict = torch.load(self.config.save_path, map_location=self.config.device)
                self.model.load_state_dict(state_dict)
                print("[AI Predictor] Model weights loaded successfully.")
            except Exception as e:
                raise RuntimeError(f"FATAL: Error loading model weights: {e}")
        else:
            raise RuntimeError(f"FATAL: Model file not found at {self.config.save_path}")

        self.model.eval()
        print(f"[AI Predictor] Initialized successfully with {num_classes} classes.")

    def _load_classes(self):
        """
        Loads class names from the training directory structure.
        """
        try:
            train_dir = self.config.train_dir
            if os.path.exists(train_dir):
                classes = sorted([d for d in os.listdir(train_dir) if os.path.isdir(os.path.join(train_dir, d))])
                idx_to_class = {i: c for i, c in enumerate(classes)}
                return classes, idx_to_class
            else:
                print(
                    f"[AI Predictor] Warning: Train dir {self.config.train_dir} not found. Class mapping will be empty.")
                return [], {}
        except Exception as e:
            print(f"[AI Predictor] Error loading classes: {e}")
            return [], {}

    def predict(self, image_bytes: bytes):
        """
        Takes image bytes, preprocesses (including 4th channel), and returns prediction.
        """
        transform = transforms.Compose([
            transforms.Resize((self.config.image_size, self.config.image_size)),
            transforms.ToTensor(),
        ])

        try:
            img = Image.open(BytesIO(image_bytes)).convert("RGB")

            # 1. Standard transformation (Resize + ToTensor) -> [3, H, W]
            x = transform(img).unsqueeze(0)  # [1, 3, H, W]

            # 2. Add 4th channel if config requires it (DenseNetBackbone uses 4)
            if self.config.input_channels == 4:
                extra_channel = torch.ones(
                    1, 1,
                    self.config.image_size, self.config.image_size
                )
                x = torch.cat([x, extra_channel], dim=1)  # [1, 4, H, W]

            x = x.to(self.config.device)

            with torch.no_grad():
                logits, _ = self.model(x)
                probs = torch.softmax(logits, dim=1)

            pred_idx = probs.argmax().item()
            confidence = probs[0][pred_idx].item()

            if self.idx_to_class:
                label = self.idx_to_class.get(pred_idx, f"Class {pred_idx}")
            else:
                label = f"Class {pred_idx}"

            return {
                "predicted_class": label,
                "probability": f"{confidence:.4f}"
            }

        except Exception as e:
            print(f"Prediction Error: {e}")
            return {"error": str(e)}