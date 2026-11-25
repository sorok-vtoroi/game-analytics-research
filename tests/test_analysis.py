"""Проверки воспроизводимости анализа исходной Unity-сессии."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.analyze import DEFAULT_INPUT, analyze  # noqa: E402


class TestUnityLog(unittest.TestCase):
    def test_counts(self):
        result, _ = analyze(DEFAULT_INPUT)
        self.assertEqual(result["events_total"], 123)
        self.assertEqual(result["hits"], 62)
        self.assertEqual(result["misses"], 40)
        self.assertEqual(result["moves"], 21)
        self.assertEqual(result["sessions"], 1)

    def test_reaction_metrics(self):
        result, outliers = analyze(DEFAULT_INPUT)
        self.assertEqual(result["mean_seconds"], 0.925)
        self.assertEqual(result["median_seconds"], 0.612)
        self.assertEqual(result["std_seconds_sample"], 1.369)
        self.assertEqual(len(outliers), 5)

    def test_click_accuracy(self):
        result, _ = analyze(DEFAULT_INPUT)
        self.assertAlmostEqual(result["click_accuracy_percent"], 60.784, places=3)


if __name__ == "__main__":
    unittest.main()
