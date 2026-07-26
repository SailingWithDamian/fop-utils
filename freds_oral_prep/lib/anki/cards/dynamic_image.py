import dataclasses
import json
from typing import Any


@dataclasses.dataclass(frozen=True)
class DynamicImageCard:
    MODEL_NAME = "Dynamic Image"

    title: str
    question: str
    description: str
    board_points: tuple[dict[str, Any], ...]
    grid_is_black: bool
    categories: tuple[dict[str, Any], ...]
    explanation: str | None = None
    tags: tuple[str, ...] = ()

    def get_note_data(self) -> dict[str, Any]:
        note = {
            "Title": self.title,
            "Question": self.question,
            "Description": self.description,
            "Board": json.dumps({"gridIsBlack": self.grid_is_black, "points": list(self.board_points)}),
            "Categories": json.dumps(list(self.categories)),
        }
        if self.explanation is not None:
            note["Explanation"] = self.explanation
        return note

    def get_question_data(self) -> dict[str, Any]:
        return {
            "Title": self.title,
            "Question": self.question,
            "Description": self.description,
            "Board": json.dumps({"gridIsBlack": self.grid_is_black, "points": list(self.board_points)}),
        }
