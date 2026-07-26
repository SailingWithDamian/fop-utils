import json
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup

from freds_oral_prep.mca.exam_finder.models import Exam, Slot


class McaOnlineExamSchedule:
    _ALLOWED_SLOT_DAYS_AND_TIMES: dict[int, tuple[set[int], set[tuple[int, int]]]] = {
        90: ({0, 4}, {(9, 0), (10, 45), (13, 0), (14, 45)}),  # Masters: Mon/Fri
        120: ({1, 2, 3}, {(9, 0), (11, 30), (14, 30)}),  # OOW: Tue/Wed/Thu
    }

    def __init__(self) -> None:
        self._session = requests.Session()
        self._session.headers["User-Agent"] = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/149.0.0.0 Safari/537.36"
        )
        self._session_token: str | None = None

    def _get_csrf_token(self) -> str | None:
        r = self._session.get("https://mymca-prod.powerappsportals.com/_layout/tokenhtml")
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        if elem := soup.find("input", {"name": "__RequestVerificationToken"}):
            return elem.get("value")
        return None

    def _post_trigger(self, trigger_id: str, event_data: dict) -> dict:
        csrf_token = self._get_csrf_token()
        if not csrf_token:
            raise RuntimeError("Unable to obtain CSRF token")

        r = self._session.post(
            f"https://mymca-prod.powerappsportals.com/_api/cloudflow/v1.0/trigger/{trigger_id}",
            headers={
                "__requestverificationtoken": csrf_token,
                "X-Requested-With": "XMLHttpRequest",
            },
            json={"eventData": json.dumps(event_data)},
        )
        r.raise_for_status()
        return r.json()

    def _allowed_start_times(self, slot: Slot, duration_minutes: int) -> list[datetime]:
        try:
            allowed_weekdays, allowed_times = self._ALLOWED_SLOT_DAYS_AND_TIMES[duration_minutes]
        except KeyError:
            raise ValueError(f"Unsupported duration: {duration_minutes}") from None

        return [
            start
            for start in slot.available_start_times
            if start.weekday() in allowed_weekdays and (start.hour, start.minute) in allowed_times
        ]

    def login(self, seafarer_reference_number: str, date_of_birth: date) -> bool:
        data = self._post_trigger(
            "3a0546c0-bb8d-f011-b4cb-002248c69102",
            {
                "dateOfBirth": date_of_birth.strftime("%Y-%m-%d"),
                "seafarerReference": seafarer_reference_number,
            },
        )
        if data.get("status") != "success":
            return False

        self._session_token = data["token"]
        return True

    def find_exams(self) -> list[Exam]:
        data = self._post_trigger(
            "3c821dee-a2b8-f011-bbd3-6045bd0c6530",
            {
                "sessionToken": self._session_token,
            },
        )
        return [Exam.from_api(exam) for exam in json.loads(data["data"])]

    def find_slots(self, exam: Exam, start_date: date, end_date: date) -> list[Slot]:
        data = self._post_trigger(
            "94b3765c-a0a2-f011-bbd2-002248c6910a",
            {
                "workorderguid": exam.guid,
                "token": self._session_token,
                "fromdate": start_date.strftime("%Y-%m-%d"),
                "todate": end_date.strftime("%Y-%m-%d"),
                "examName": exam.name,
            },
        )
        duration_minutes = int(data["duration"])
        slots = []
        for raw_slot in json.loads(data["slots"]):
            slot = Slot.from_api(raw_slot)
            if allowed_starts := self._allowed_start_times(slot, duration_minutes):
                slots.append(Slot(available_start_times=allowed_starts))
        return slots
