import logging
import time

import schedule
from schedule import Job

from synchronizer import dir_sync

log = logging.getLogger('job.job_runner.JobRunner')


class JobRunnerException(Exception):
    pass


class JobRunner:

    def __init__(self, input_dir: str, output_dir: str, time_frame: str = None):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.time_frame = time_frame
        self.is_running = True

    def run_job(self):
        sync = dir_sync.Synchronizer()
        if self.time_frame is None:
            log.info("Synchronization execution started")
            sync.synchronize(self.input_dir, self.output_dir)
        else:
            self.__create_timed_scheduler().do(sync.synchronize, self.input_dir, self.output_dir)
            log.info("Synchronization job started with interval %s", self.time_frame)

            while self.is_running:
                schedule.run_pending()
                time.sleep(1)

    def stop(self):
        self.is_running = False

    def __create_timed_scheduler(self) -> Job:
        unit = self.time_frame[-1]
        value = self.time_frame.removesuffix(unit)
        if not value.isdigit():
            raise JobRunnerException(f"Wrong time value was provided: '{self.time_frame}'")
        value = int(value)

        prepared_schedule = schedule.every(value)
        match unit:
            case 's':
                return prepared_schedule.seconds
            case 'm':
                return prepared_schedule.minutes
            case 'h':
                return prepared_schedule.hours
            case 'd':
                return prepared_schedule.days
            case _:
                raise JobRunnerException(f"Unknown time unit was used: '{unit}'")
