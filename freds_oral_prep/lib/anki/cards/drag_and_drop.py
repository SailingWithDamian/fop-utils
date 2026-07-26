import dataclasses
from typing import Any


@dataclasses.dataclass(frozen=True)
class DragAndDropCard:
    MODEL_NAME = "Drag & Drop"

    title: str
    question: str
    question_1: str | None = None
    answer_1: str | None = None
    question_2: str | None = None
    answer_2: str | None = None
    question_3: str | None = None
    answer_3: str | None = None
    question_4: str | None = None
    answer_4: str | None = None
    question_5: str | None = None
    answer_5: str | None = None
    question_6: str | None = None
    answer_6: str | None = None
    question_7: str | None = None
    answer_7: str | None = None
    question_8: str | None = None
    answer_8: str | None = None
    question_9: str | None = None
    answer_9: str | None = None
    question_10: str | None = None
    answer_10: str | None = None
    explanation: str | None = None
    tags: tuple[str, ...] = ()

    def get_note_data(self) -> dict[str, Any]:
        note = {"Title": self.title, "Question": self.question}
        for x in range(1, 11):
            if getattr(self, f"question_{x}") is not None:
                note[f"Q_{x}"] = getattr(self, f"question_{x}")
            if getattr(self, f"answer_{x}") is not None:
                note[f"A_{x}"] = getattr(self, f"answer_{x}")
        if self.explanation is not None:
            note["Explanation"] = self.explanation
        return note

    def get_question_data(self) -> dict[str, Any]:
        note = {"Title": self.title, "Question": self.question}
        for x in range(1, 11):
            if getattr(self, f"question_{x}") is not None:
                note[f"Q_{x}"] = getattr(self, f"question_{x}")
        return note
