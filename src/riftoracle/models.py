from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class WinChanceModel(Protocol):
    def fit(self, X: list[list[float]], y: list[int]) -> None: ...

    def predict_proba(self, X: list[list[float]]) -> list[float]: ...


@dataclass
class LogisticRegressionWinModel:
    random_state: int = 42
    max_iter: int = 200

    def __post_init__(self) -> None:
        try:
            from sklearn.linear_model import LogisticRegression
        except ImportError as exc:
            raise ImportError(
                "scikit-learn is required for LogisticRegressionWinModel. "
                "Install dependencies with `pip install -r requirements.txt`."
            ) from exc

        self._model = LogisticRegression(
            max_iter=self.max_iter,
            random_state=self.random_state,
        )

    def fit(self, X: list[list[float]], y: list[int]) -> None:
        self._model.fit(X, y)

    def predict_proba(self, X: list[list[float]]) -> list[float]:
        return self._model.predict_proba(X)[:, 1].tolist()


@dataclass
class RandomForestWinModel:
    random_state: int = 42
    n_estimators: int = 300

    def __post_init__(self) -> None:
        try:
            from sklearn.ensemble import RandomForestClassifier
        except ImportError as exc:
            raise ImportError(
                "scikit-learn is required for RandomForestWinModel. "
                "Install dependencies with `pip install -r requirements.txt`."
            ) from exc

        self._model = RandomForestClassifier(
            n_estimators=self.n_estimators,
            random_state=self.random_state,
            n_jobs=-1,
        )

    def fit(self, X: list[list[float]], y: list[int]) -> None:
        self._model.fit(X, y)

    def predict_proba(self, X: list[list[float]]) -> list[float]:
        return self._model.predict_proba(X)[:, 1].tolist()
