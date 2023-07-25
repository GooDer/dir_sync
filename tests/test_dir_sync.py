"""
Environment parameter DEBUG=1 can be used to print during run of the tests structure of source and target folder.
That can be handy in case of some failing test and could be extended in future to also provide more detailed information
on the files and directories
"""
import glob
import os
import re
import shutil
from stat import S_IREAD, S_IRGRP, S_IROTH, S_IWUSR
import unittest

from synchronizer.dir_sync import Synchronizer, SynchronizerException

SYNC_OUTPUT = 'data' + os.sep + 'target'
SYNC_INPUT = 'data' + os.sep + 'source'

SYNC_LOGGER = 'synchronizer.dir_sync.Synchronizer'
DEBUG_HEADER = 'before synchronization'
DIF_LOG_COUNT_MSG = 'Expected different number of log entries'

FILE_NAME1 = 'test_file1.txt'
FILE_NAME2 = 'test_file2.txt'
FILE_NAME3 = 'test_file3.txt'


class SynchronizerTest(unittest.TestCase):

    def setUp(self):
        self.doCleanups()

        if not os.path.exists(SYNC_OUTPUT):
            os.mkdir(SYNC_OUTPUT)

        if not os.path.exists(SYNC_INPUT):
            os.mkdir(SYNC_INPUT)

        self.__create_sub_dir('sub_folder')
        self.__create_file(FILE_NAME1, 'some test text')
        self.__create_file(FILE_NAME3, '...')
        self.__create_file(f'sub_folder/{FILE_NAME2}', 'sub folder test file')

    def doCleanups(self):
        # make files back writable
        for file in glob.glob('data' + os.sep + '**', recursive=True):
            os.chmod(file, S_IWUSR | S_IREAD)

        if os.path.exists(SYNC_OUTPUT):
            shutil.rmtree(SYNC_OUTPUT)

        if os.path.exists(SYNC_INPUT):
            shutil.rmtree(SYNC_INPUT)

    def test_basic_synchronization_without_separator(self):
        self.__print_debug(DEBUG_HEADER)

        synchronizer = Synchronizer()
        with self.assertLogs(SYNC_LOGGER, level='INFO') as cm:
            synchronizer.synchronize(SYNC_INPUT, SYNC_OUTPUT)
            self.assertEqual(5, len(cm.records), DIF_LOG_COUNT_MSG)
            self.assertEqual(f"Started with synchronization of {SYNC_INPUT} to {SYNC_OUTPUT}",
                             cm.records[0].getMessage())
            self.assert_log_missing_directory(cm.records[1].getMessage(), 'sub_folder')
            self.assert_log_missing_file(cm.records[2].getMessage(), 'sub_folder', FILE_NAME2)
            self.assert_log_missing_file(cm.records[3].getMessage(), FILE_NAME1)
            self.assert_log_missing_file(cm.records[4].getMessage(), FILE_NAME3)

        self.__compare_source_and_target()

    def test_basic_synchronization_with_separator(self):
        self.__print_debug(DEBUG_HEADER)

        synchronizer = Synchronizer()
        with self.assertLogs(SYNC_LOGGER, level='INFO') as cm:
            synchronizer.synchronize(SYNC_INPUT + os.sep, SYNC_OUTPUT + os.sep)

            self.assertEqual(5, len(cm.records), DIF_LOG_COUNT_MSG)
            self.assertEqual(f"Started with synchronization of {SYNC_INPUT + os.sep} to {SYNC_OUTPUT + os.sep}",
                             cm.records[0].getMessage())
            self.assert_log_missing_directory(cm.records[1].getMessage(), 'sub_folder')
            self.assert_log_missing_file(cm.records[2].getMessage(), 'sub_folder', FILE_NAME2)
            self.assert_log_missing_file(cm.records[3].getMessage(), FILE_NAME1)
            self.assert_log_missing_file(cm.records[4].getMessage(), FILE_NAME3)

        self.__compare_source_and_target()

    def test_change_in_file(self):
        synchronizer = Synchronizer()
        synchronizer.synchronize(SYNC_INPUT, SYNC_OUTPUT)

        # different file size
        self.__create_file(FILE_NAME1, 'some test text and longer text')
        # different file modification time
        self.__create_file(FILE_NAME3, '+++')
        # new file
        self.__create_file('test_file_new.txt', 'newly created file')
        self.__create_file('sub_folder/test_sub_file_new.txt', 'newly created sub file')

        self.__print_debug(DEBUG_HEADER)

        with self.assertLogs(SYNC_LOGGER, level='INFO') as cm:
            synchronizer.synchronize(SYNC_INPUT, SYNC_OUTPUT)

            self.assertEqual(5, len(cm.records), DIF_LOG_COUNT_MSG)
            self.assertEqual(f"Started with synchronization of {SYNC_INPUT} to {SYNC_OUTPUT}",
                             cm.records[0].getMessage())
            self.assert_log_missing_file(cm.records[1].getMessage(), 'sub_folder', 'test_sub_file_new.txt')
            self.assert_log_changed_meta(cm.records[2].getMessage(), FILE_NAME1)
            self.assert_log_changed_meta(cm.records[3].getMessage(), FILE_NAME3)
            self.assert_log_missing_file(cm.records[4].getMessage(), 'test_file_new.txt')

        self.__compare_source_and_target()

    def test_change_in_directory(self):
        synchronizer = Synchronizer()
        synchronizer.synchronize(SYNC_INPUT, SYNC_OUTPUT)

        self.__create_sub_dir('new_sub_directory')
        self.__create_file('new_sub_directory/new_file_in_sub_directory.txt', '.,.,.,.,.,')

        os.renames(SYNC_INPUT + os.sep + 'sub_folder', SYNC_INPUT + os.sep + 'something_different')

        self.__print_debug(DEBUG_HEADER)

        with self.assertLogs(SYNC_LOGGER, level='INFO') as cm:
            synchronizer.synchronize(SYNC_INPUT, SYNC_OUTPUT)

            self.assertEqual(6, len(cm.records), DIF_LOG_COUNT_MSG)
            self.assertEqual(f"Started with synchronization of {SYNC_INPUT} to {SYNC_OUTPUT}",
                             cm.records[0].getMessage())
            self.assert_log_missing_directory(cm.records[1].getMessage(), 'new_sub_directory')
            self.assert_log_missing_file(cm.records[2].getMessage(), 'new_sub_directory',
                                         'new_file_in_sub_directory.txt')
            self.assert_log_missing_directory(cm.records[3].getMessage(), 'something_different')
            self.assert_log_missing_file(cm.records[4].getMessage(), 'something_different', FILE_NAME2)

        self.__compare_source_and_target()

    def test_change_in_file_mod(self):
        synchronizer = Synchronizer()
        synchronizer.synchronize(SYNC_INPUT, SYNC_OUTPUT)

        os.chmod(SYNC_INPUT + os.sep + FILE_NAME1, S_IREAD|S_IRGRP|S_IROTH)

        with self.assertLogs(SYNC_LOGGER, level='INFO') as cm:
            synchronizer.synchronize(SYNC_INPUT, SYNC_OUTPUT)

            self.assertEqual(2, len(cm.records), DIF_LOG_COUNT_MSG)
            self.assertEqual(f"Started with synchronization of {SYNC_INPUT} to {SYNC_OUTPUT}",
                             cm.records[0].getMessage())
            self.assert_log_changed_mode(cm.records[1].getMessage(), FILE_NAME1)

        self.__compare_source_and_target()

    def test_non_existing_source(self):
        synchronizer = Synchronizer()
        with self.assertRaisesRegex(SynchronizerException, "Wrong input directory was provided"):
            synchronizer.synchronize('non_existing_folder', SYNC_OUTPUT)

    def test_non_existing_target(self):
        synchronizer = Synchronizer()
        with self.assertRaisesRegex(SynchronizerException, "Wrong output directory was provided"):
            synchronizer.synchronize(SYNC_INPUT, 'non_existing_folder')

    def __compare_files(self, input_f: str, output_f: str):
        input_stat = os.stat(input_f)
        output_stat = os.stat(output_f)

        file_log = f"for {input_f} and {output_f} files"

        self.assertEqual(input_stat.st_size, output_stat.st_size, f"Size of files doesn't match {file_log}")
        self.assertEqual(input_stat.st_mtime, output_stat.st_mtime,
                         f"Modification time of files doesn't match {file_log}")
        self.assertEqual(input_stat.st_mode, output_stat.st_mode, f"File mode doesn't match {file_log}")
        self.assertEqual(input_stat.st_uid, output_stat.st_uid, f"File owner doesn't match {file_log}")
        self.assertEqual(input_stat.st_gid, output_stat.st_gid, f"File group doesn't match {file_log}")

        with open(input_f, 'r', encoding="utf-8") as input_file, open(output_f, 'r', encoding="utf-8") as output_file:
            self.assertListEqual(input_file.readlines(), output_file.readlines(),
                                 f"File content doesn't match {file_log}")

    def __compare_source_and_target(self):
        self.__print_debug('compare source and target')
        for input_file in glob.glob(SYNC_INPUT + os.sep + '**', recursive=True):
            expected_file = input_file.replace(SYNC_INPUT, SYNC_OUTPUT)
            if input_file == SYNC_INPUT + os.sep:
                # skip folder itself
                continue
            self.assertTrue(os.path.exists(expected_file), f"file or directory {input_file} doesn't exists in replica")
            if os.path.isfile(input_file):
                self.__compare_files(input_file, expected_file)

    def assert_log_missing_file(self, msg: str, *parts: str):
        self.assertEqual(f"Copying missing file '{self.__prepare_path(*parts)}' to replica", msg)

    def assert_log_missing_directory(self, msg: str, *parts: str):
        self.assertEqual(f"Creating new directory '{self.__prepare_path(*parts)}' in replica", msg)

    def assert_log_changed_meta(self, msg, *parts: str):
        self.assertRegex(msg, f"Updating file with changed metadata '{self.__prepare_regexp_path(*parts)}':"
                              " original -> {.*}, replica -> {.*}")

    def assert_log_changed_mode(self, msg, *parts: str):
        self.assertRegex(msg, f"Updating file mode '{self.__prepare_regexp_path(*parts)}':"
                              r' original -> \d*, replica -> \d*')

    @staticmethod
    def __create_file(file_name: str, content: str):
        with open(SYNC_INPUT + os.sep + file_name, "w", encoding="utf-8") as file:
            file.write(content)

    @staticmethod
    def __create_sub_dir(directory: str):
        os.mkdir(SYNC_INPUT + os.sep + directory)

    @staticmethod
    def __prepare_path(*parts: str) -> str:
        return SYNC_OUTPUT + os.sep + os.sep.join(parts)

    @staticmethod
    def __prepare_regexp_path(*parts: str) -> str:
        return re.escape(SYNC_OUTPUT + os.sep + os.sep.join(parts))

    @staticmethod
    def __print_debug(header: str):
        if os.environ.get('DEBUG'):
            print(f"-----------{header}----------")
            print("State of input folder:")
            print(*glob.glob(SYNC_INPUT + os.sep + '**', recursive=True), sep='\n')
            print("------------------------")
            print("state of output folder:")
            print(*glob.glob(SYNC_OUTPUT + os.sep + '**', recursive=True), sep='\n')
            print("-----------END----------")


if __name__ == '__main__':
    unittest.main()
