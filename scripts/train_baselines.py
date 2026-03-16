#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split

from riftoracle.data import load_match_examples
from riftoracle.features import build_feature_matrix
from riftoracle.models import LogisticRegressionWinModel, RandomForestWinModel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train baseline win chance models.")
    parser.add_argument("--matches-dir", type=Path, required=True)
    parser.add_argument("--sample-size", type=int, default=1000)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


def evaluate_predictions(y_true: list[int], probabilities: list[float]) -> tuple[float, float]:
    predictions = [1 if probability >= 0.5 else 0 for probability in probabilities]
    accuracy = accuracy_score(y_true, predictions)
    auc = roc_auc_score(y_true, probabilities)
    return accuracy, auc


def validate_training_data(sample_count: int, labels: list[int], test_size: float) -> None:
    if sample_count < 20:
        raise SystemExit(
            "Not enough examples to train. The bundled data-collection/matches directory is "
            "sample data only and may be too small. Collect more matches with "
            "`python -m riftoracle.collect --matches-per-tier 100` and try again."
        )

    unique_labels = sorted(set(labels))
    if len(unique_labels) < 2:
        raise SystemExit(
            "Training requires both blue-win and red-win examples. The current dataset only "
            "contains one class, so stratified splitting cannot proceed."
        )

    test_count = max(1, int(round(sample_count * test_size)))
    train_count = sample_count - test_count
    minority_class_count = min(labels.count(label) for label in unique_labels)
    if (
        test_count < len(unique_labels)
        or train_count < len(unique_labels)
        or minority_class_count < 2
    ):
        raise SystemExit(
            "Not enough class-balanced data for the requested train/test split. Add more match "
            "files or adjust --test-size after collecting more data."
        )


def main() -> None:
    args = parse_args()

    examples = load_match_examples(args.matches_dir, sample_size=args.sample_size)
    fm = build_feature_matrix(examples)
    validate_training_data(len(examples), fm.y, args.test_size)

    X_train, X_test, y_train, y_test = train_test_split(
        fm.X,
        fm.y,
        test_size=args.test_size,
        random_state=args.random_state,
        stratify=fm.y,
    )

    models = {
        "logistic_regression": LogisticRegressionWinModel(random_state=args.random_state),
        "random_forest": RandomForestWinModel(random_state=args.random_state),
    }

    for name, model in models.items():
        model.fit(X_train, y_train)
        proba = model.predict_proba(X_test)
        acc, auc = evaluate_predictions(y_test, proba)
        print(f"{name}: accuracy={acc:.4f} auc={auc:.4f}")


if __name__ == "__main__":
    main()
