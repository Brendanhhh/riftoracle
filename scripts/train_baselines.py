#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from sklearn.model_selection import train_test_split

from riftoracle.data import load_match_examples
from riftoracle.features import build_feature_matrix
from riftoracle.models import LogisticRegressionWinModel, RandomForestWinModel
from riftoracle.training import evaluate_predictions, validate_training_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train baseline win chance models.")
    parser.add_argument("--matches-dir", type=Path, required=True)
    parser.add_argument("--sample-size", type=int, default=1000)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


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
