"""RiftOracle package for win chance modeling from League match JSON data."""

from .data import MatchExample, load_match_examples
from .features import FeatureMatrix, build_feature_matrix
from .models import (
    LogisticRegressionWinModel,
    RandomForestWinModel,
    WinChanceModel,
)

__all__ = [
    "FeatureMatrix",
    "LogisticRegressionWinModel",
    "MatchExample",
    "RandomForestWinModel",
    "WinChanceModel",
    "build_feature_matrix",
    "load_match_examples",
]
