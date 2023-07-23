import schedule
import time

from synchronizer.dir_sync import Synchronizer


class JobRunner:

    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = input_dir
        self.output_dir = output_dir

    def run_job(self):
        sync = Synchronizer()
        schedule.every(10).seconds.do(sync.synchronize, self.input_dir, self.output_dir)

        while True:
            schedule.run_pending()
            time.sleep(1)
