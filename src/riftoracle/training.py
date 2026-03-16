from __future__ import annotations

from sklearn.metrics import accuracy_score, roc_auc_score


def evaluate_predictions(
    y_true: list[int],
    probabilities: list[float],
) -> tuple[float, float]:
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
