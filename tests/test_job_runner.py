import unittest
from unittest.mock import patch, MagicMock

from job.job_runner import JobRunner, JobRunnerException
import schedule

INPUT_DIR = 'some/directory'
OUTPUT_DIR = 'destination/directory'


class MyTestCase(unittest.TestCase):

    @patch("synchronizer.dir_sync.Synchronizer")
    def test_job_run_without_interval(self, sync: MagicMock):
        sync_instance = self.__prepare_job_runner(sync, None)

        sync_instance.synchronize.assert_called_once_with(INPUT_DIR, OUTPUT_DIR)

    @patch("synchronizer.dir_sync.Synchronizer")
    def test_job_run_with_seconds_interval(self, sync: MagicMock):
        unit_mock = MagicMock(name="every")
        with patch.object(schedule, 'every', return_value=unit_mock) as mock_method:
            sync_instance = self.__prepare_job_runner(sync, '3s')

            mock_method.assert_called_with(3)
            unit_mock.seconds.do.assert_called_once_with(sync_instance.synchronize, INPUT_DIR, OUTPUT_DIR)

    @patch("synchronizer.dir_sync.Synchronizer")
    def test_job_run_with_minutes_interval(self, sync: MagicMock):
        unit_mock = MagicMock(name="every")
        with patch.object(schedule, 'every', return_value=unit_mock) as mock_method:
            sync_instance = self.__prepare_job_runner(sync, '3m')

            mock_method.assert_called_with(3)
            unit_mock.minutes.do.assert_called_once_with(sync_instance.synchronize, INPUT_DIR, OUTPUT_DIR)

    @patch("synchronizer.dir_sync.Synchronizer")
    def test_job_run_with_hours_interval(self, sync: MagicMock):
        unit_mock = MagicMock(name="every")
        with patch.object(schedule, 'every', return_value=unit_mock) as mock_method:
            sync_instance = self.__prepare_job_runner(sync, '3h')

            mock_method.assert_called_with(3)
            unit_mock.hours.do.assert_called_once_with(sync_instance.synchronize, INPUT_DIR, OUTPUT_DIR)

    @patch("synchronizer.dir_sync.Synchronizer")
    def test_job_run_with_days_interval(self, sync: MagicMock):
        unit_mock = MagicMock(name="every")
        with patch.object(schedule, 'every', return_value=unit_mock) as mock_method:
            sync_instance = self.__prepare_job_runner(sync, '3d')

            mock_method.assert_called_with(3)
            unit_mock.days.do.assert_called_once_with(sync_instance.synchronize, INPUT_DIR, OUTPUT_DIR)

    @patch("synchronizer.dir_sync.Synchronizer")
    def test_job_run_with_unknown_time_unit(self, sync: MagicMock):
        unit_mock = MagicMock(name="every")
        with patch.object(schedule, 'every', return_value=unit_mock):
            self.assertRaisesRegex(JobRunnerException, "Unknown time unit was used: 'k'", self.__prepare_job_runner,
                                   sync, '3k')

    @patch("synchronizer.dir_sync.Synchronizer")
    def test_job_run_with_wrong_time_value(self, sync: MagicMock):
        unit_mock = MagicMock(name="every")
        with patch.object(schedule, 'every', return_value=unit_mock):
            self.assertRaisesRegex(JobRunnerException, "Wrong time value was provided: 'ah'", self.__prepare_job_runner,
                                   sync, 'ah')

    @staticmethod
    def __prepare_job_runner(sync: MagicMock, unit: str):
        sync_instance = MagicMock(name="syncInstance")
        sync.return_value = sync_instance
        job = JobRunner(INPUT_DIR, OUTPUT_DIR, unit)
        job.stop()
        job.run_job()
        return sync_instance


if __name__ == '__main__':
    unittest.main()
