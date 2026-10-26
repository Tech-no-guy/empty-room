"""
Empty Room - Biometric Face Recognition Engine.
Handles Haar Cascade face detection, LBPH model training, face enrollment,
and biometric verification.
"""

import datetime
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from empty_room.constants import get_cascade_path, get_model_path


class FaceEngine:
    """Manages face detection and LBPH recognition."""
    
    def __init__(self):
        self.cascade_path = get_cascade_path()
        self.cascade = cv2.CascadeClassifier(self.cascade_path)
        self.model_path = get_model_path()
        self.recognizer = None
        self._load_recognizer()

    def _get_meta_path(self) -> Path:
        """Metadata path associated with the trained model."""
        return self.model_path.with_name("face_meta.json")

    def _load_recognizer(self) -> bool:
        """Load the trained recognizer if available."""
        if not self.model_path.is_file():
            self.recognizer = None
            return False
            
        try:
            self.recognizer = cv2.face.LBPHFaceRecognizer_create()
            self.recognizer.read(str(self.model_path))
            return True
        except Exception as e:
            print(f"[FACE_ENGINE] Failed to read face model: {e}")
            self.recognizer = None
            return False

    def is_trained(self) -> bool:
        """Check if an authorized face model exists and is loaded."""
        return self.recognizer is not None and self.model_path.is_file()

    def detect_faces(self, gray_frame: np.ndarray, scale_factor: float = 1.2, min_neighbors: int = 5) -> List[Tuple[int, int, int, int]]:
        """Detect frontal face rectangles in a grayscale frame."""
        if self.cascade.empty():
            # Reload cascade if necessary
            self.cascade = cv2.CascadeClassifier(self.cascade_path)
            if self.cascade.empty():
                return []
                
        faces = self.cascade.detectMultiScale(
            gray_frame,
            scaleFactor=scale_factor,
            minNeighbors=min_neighbors,
            minSize=(30, 30)
        )
        if len(faces) == 0:
            return []
        return [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces]

    def verify_face(self, face_crop: np.ndarray, threshold: float = 75.0) -> Tuple[bool, float]:
        """
        Predict identity for a face crop using LBPH.
        Returns: (is_authorized, confidence_distance)
        Lower distance = higher similarity.
        """
        if not self.is_trained() or self.recognizer is None:
            # If no model is trained, any detected face is considered present (basic mode)
            return True, 0.0

        try:
            # Standardize crop size
            resized = cv2.resize(face_crop, (120, 120))
            face_id, distance = self.recognizer.predict(resized)
            is_authorized = bool(distance < threshold)
            return is_authorized, float(distance)
        except Exception as e:
            print(f"[FACE_ENGINE] Error during prediction: {e}")
            return False, 999.0

    def train(self, face_samples: List[np.ndarray], label_id: int = 1) -> bool:
        """
        Train LBPH model from collected grayscale face samples.
        Saves the model and metadata.
        """
        if not face_samples:
            return False

        try:
            standardized = []
            labels = []
            for crop in face_samples:
                if len(crop.shape) == 3:
                    crop = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                resized = cv2.resize(crop, (120, 120))
                # Apply histogram equalization for lighting invariance
                equalized = cv2.equalizeHist(resized)
                standardized.append(equalized)
                labels.append(label_id)

            recognizer = cv2.face.LBPHFaceRecognizer_create()
            recognizer.train(standardized, np.array(labels, dtype=np.int32))
            
            # Ensure target directory exists
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            recognizer.write(str(self.model_path))
            self.recognizer = recognizer

            # Save metadata
            meta = {
                "enrolled_at": datetime.datetime.now().isoformat(),
                "samples_count": len(standardized),
                "model_format": "OpenCV LBPH",
                "label_id": label_id
            }
            with open(self._get_meta_path(), "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

            return True
        except Exception as e:
            print(f"[FACE_ENGINE] Training failed: {e}")
            return False

    def delete_model(self) -> bool:
        """Remove the enrolled face model and metadata."""
        deleted = False
        try:
            if self.model_path.is_file():
                self.model_path.unlink()
                deleted = True
            meta_path = self._get_meta_path()
            if meta_path.is_file():
                meta_path.unlink()
            self.recognizer = None
            return deleted
        except Exception as e:
            print(f"[FACE_ENGINE] Failed to delete model: {e}")
            return False

    def get_info(self) -> Dict[str, Any]:
        """Return status information about the face engine and enrolled profile."""
        meta = {}
        meta_path = self._get_meta_path()
        if meta_path.is_file():
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
            except Exception:
                pass

        return {
            "trained": self.is_trained(),
            "model_path": str(self.model_path),
            "cascade_path": str(self.cascade_path),
            "enrolled_at": meta.get("enrolled_at"),
            "samples_count": meta.get("samples_count", 0)
        }
