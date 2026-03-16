from __future__ import annotations

import unittest

from scripts.train_baselines import evaluate_predictions, validate_training_data


class TrainingHelpersTests(unittest.TestCase):
    def test_evaluate_predictions_returns_accuracy_and_auc(self) -> None:
        accuracy, auc = evaluate_predictions([1, 1, 0, 0], [0.9, 0.7, 0.4, 0.1])

        self.assertEqual(accuracy, 1.0)
        self.assertEqual(auc, 1.0)

    def test_validate_training_data_rejects_too_few_examples(self) -> None:
        with self.assertRaises(SystemExit):
            validate_training_data(10, [1, 0] * 5, 0.2)

    def test_validate_training_data_rejects_single_class(self) -> None:
        with self.assertRaises(SystemExit):
            validate_training_data(20, [1] * 20, 0.2)

    def test_validate_training_data_accepts_balanced_split(self) -> None:
        validate_training_data(20, [1, 0] * 10, 0.2)


if __name__ == "__main__":
    unittest.main()
