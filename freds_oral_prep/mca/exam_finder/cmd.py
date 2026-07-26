import logging
from datetime import date, datetime, timedelta

import click

from freds_oral_prep.mca.exam_finder.api import McaOnlineExamSchedule
from freds_oral_prep.mca.exam_finder.helpers import group_slots_by_date

logger = logging.getLogger(__name__)


@click.command()
@click.option("--seafarer-reference-number", required=True, help="MCA seafarer reference number")
@click.option("--date-of-birth", required=True, help="Date of birth, DD/MM/YYYY")
@click.option(
    "--look-ahead-weeks",
    type=int,
    default=12,
    show_default=True,
    help="How many weeks ahead to search for slots",
)
@click.pass_context
def cli(ctx, seafarer_reference_number: str, date_of_birth: str, look_ahead_weeks: int) -> None:
    """Search for available MCA oral exam slots and print them, grouped by date."""
    date_of_birth = datetime.strptime(date_of_birth, "%d/%m/%Y").date()

    exam_schedule = McaOnlineExamSchedule()
    if not exam_schedule.login(seafarer_reference_number, date_of_birth):
        click.echo("Failed to login", err=True)
        raise SystemExit(1)

    start_date = date.today()
    for exam in exam_schedule.find_exams():
        is_rebooking = exam.status == "Booked" and exam.previous_exam_date
        if is_rebooking:
            end_date = exam.previous_exam_date.date()
        else:
            end_date = start_date + timedelta(days=look_ahead_weeks * 7)

        click.echo(f"{exam.name}:")
        if is_rebooking:
            click.echo(f"Existing booking for {exam.previous_exam_date.date()}")
        click.echo(f"Searching between {start_date} and {end_date}")

        slots = exam_schedule.find_slots(exam, start_date, end_date)
        click.echo(f"Found {len(slots)} available slots")

        for day, day_slots in group_slots_by_date(slots):
            click.echo(f"\n{day:%A %d %B %Y}:")
            for start_time in day_slots:
                click.echo(f"  {start_time:%H:%M}")
