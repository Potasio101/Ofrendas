from typing import Tuple

from offering_app.interfaces.i_correction_strategy import ICorrectionStrategy
from offering_app.strategies.fuzzy_correction import FuzzyCorrection


class TrainedCorrection(ICorrectionStrategy):
    def __init__(self) -> None:
        # TODO: Load and use the trained model in phase 2.
        self._fallback = FuzzyCorrection()

    def correct(self, text: str, field: str, members: list[str]) -> Tuple[str, float]:
        return self._fallback.correct(text, field, members)
