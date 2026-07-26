from datetime import date, datetime

from freds_oral_prep.mca.exam_finder.models import Slot


def group_slots_by_date(all_slots: list[Slot]) -> list[tuple[date, list[datetime]]]:
    by_day: dict[date, list[datetime]] = {}
    for slot in all_slots:
        for start_time in slot.available_start_times:
            by_day.setdefault(start_time.date(), []).append(start_time)
    return [(day, sorted(by_day[day])) for day in sorted(by_day)]
