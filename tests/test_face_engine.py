"""
Unit tests for face engine and synthetic biometric training.
"""

import unittest
import numpy as np
from empty_room.face_engine import FaceEngine


class TestFaceEngine(unittest.TestCase):

    def setUp(self):
        self.engine = FaceEngine()

    def test_detect_faces_empty_canvas(self):
        blank = np.zeros((240, 320), dtype=np.uint8)
        faces = self.engine.detect_faces(blank)
        self.assertEqual(len(faces), 0)

    def test_train_synthetic_samples(self):
        # Generate synthetic face-like textures for pipeline verification
        synthetic_samples = []
        for i in range(5):
            arr = np.random.randint(50, 200, (120, 120), dtype=np.uint8)
            synthetic_samples.append(arr)

        trained = self.engine.train(synthetic_samples, label_id=1)
        self.assertTrue(trained)
        self.assertTrue(self.engine.is_trained())

        info = self.engine.get_info()
        self.assertTrue(info["trained"])
        self.assertEqual(info["samples_count"], 5)

        # Test verification
        test_crop = synthetic_samples[0]
        auth, dist = self.engine.verify_face(test_crop, threshold=120)
        self.assertIsInstance(auth, bool)
        self.assertIsInstance(dist, float)


if __name__ == "__main__":
    unittest.main()
