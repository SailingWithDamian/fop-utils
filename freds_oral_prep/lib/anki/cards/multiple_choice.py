import dataclasses
import json
from typing import Any


@dataclasses.dataclass(frozen=True)
class MultipleChoiceCard:
    MODEL_NAME = "Multiple Choice"

    title: str
    question: str
    answers: tuple[tuple[str, bool], ...]
    image: str | None = None
    explanation: str | None = None
    tags: tuple[str, ...] = ()

    def get_note_data(self) -> dict[str, Any]:
        note = {
            "Title": self.title,
            "Question": self.question,
            "Answers": json.dumps([{"text": text, "correct": correct} for text, correct in self.answers]),
        }
        if self.image is not None:
            note["Image"] = self.image
        if self.explanation is not None:
            note["Explanation"] = self.explanation
        return note

    def get_question_data(self) -> dict[str, Any]:
        return {"Title": self.title, "Question": self.question}
