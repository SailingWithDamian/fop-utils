import dataclasses
import json
from typing import Any


@dataclasses.dataclass(frozen=True)
class OrderingCard:
    MODEL_NAME = "Ordering"

    title: str
    question: str
    items: tuple[str, ...]
    explanation: str | None = None
    tags: tuple[str, ...] = ()

    def get_note_data(self) -> dict[str, Any]:
        note = {
            "Title": self.title,
            "Question": self.question,
            "Items": json.dumps(list(self.items)),
        }
        if self.explanation is not None:
            note["Explanation"] = self.explanation
        return note

    def get_question_data(self) -> dict[str, Any]:
        return {"Title": self.title, "Question": self.question}
