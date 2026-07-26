import dataclasses
from typing import Any


@dataclasses.dataclass(frozen=True)
class BasicFlipCard:
    MODEL_NAME = "Basic"

    front: str
    back: str
    tags: tuple[str, ...] = ()

    def get_note_data(self) -> dict[str, Any]:
        return {"Front": self.front, "Back": self.back}

    def get_question_data(self) -> dict[str, Any]:
        return self.get_note_data()
