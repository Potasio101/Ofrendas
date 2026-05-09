from abc import ABC, abstractmethod

from offering_app.models.correction import Correction


class ITrainingRepo(ABC):
    @abstractmethod
    def save_correction(self, correction: Correction) -> bool:
        """Persist a correction sample for future model tuning."""
