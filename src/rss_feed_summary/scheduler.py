import schedule
import time
from typing import Callable


def run_daily(hour: int, minute: int, job: Callable[[], None]):
    schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(job)
    while True:
        schedule.run_pending()
        time.sleep(30)