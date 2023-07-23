import logging
import time

import schedule
from schedule import Job

from synchronizer.dir_sync import Synchronizer

log = logging.getLogger('job.job_runner.JobRunner')


class JobRunnerException(Exception):
    pass


class JobRunner:

    def __init__(self, input_dir: str, output_dir: str, time_frame: str):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.time_frame = time_frame

    def run_job(self):
        sync = Synchronizer()
        self.__create_timed_scheduler().do(sync.synchronize, self.input_dir, self.output_dir)

        while True:
            schedule.run_pending()
            time.sleep(1)

    def __create_timed_scheduler(self) -> Job:
        unit = self.time_frame[-1]
        value = self.time_frame.removesuffix(unit)
        if not value.isdigit():
            raise JobRunnerException(f'Wrong time unit was provided: {self.time_frame}')
        value = int(value)

        log.info("Synchronization job started with interval %s", self.time_frame)

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
