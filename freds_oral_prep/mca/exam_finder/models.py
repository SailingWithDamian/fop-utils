from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

UK_TZ = ZoneInfo("Europe/London")


@dataclass(frozen=True)
class Exam:
    guid: str
    name: str
    status: str
    previous_exam_date: datetime | None

    @classmethod
    def from_api(cls, data: dict) -> "Exam":
        previous_exam_date = None
        if date_str := data.get("PreviousExamDate"):
            previous_exam_date = datetime.fromisoformat(date_str)

        return cls(
            guid=data["guid"],
            name=data["exam name"],
            status=data["status"],
            previous_exam_date=previous_exam_date,
        )


@dataclass(frozen=True)
class Slot:
    available_start_times: list[datetime]

    @classmethod
    def from_api(cls, data: dict) -> "Slot":
        return cls(
            available_start_times=[
                datetime.fromisoformat(interval["StartTime"]).replace(tzinfo=UK_TZ)
                for interval in data["Availability"]["AvailableIntervals"]
            ],
        )
