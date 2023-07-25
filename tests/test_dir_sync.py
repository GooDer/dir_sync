import glob
import os
import re
import shutil
from stat import S_IREAD, S_IRGRP, S_IROTH, S_IWUSR
import unittest

from synchronizer.dir_sync import Synchronizer

SYNC_OUTPUT = 'data' + os.sep + 'target'
SYNC_INPUT = 'data' + os.sep + 'source'


class SynchronizerTest(unittest.TestCase):

    def setUp(self):
        # make files back writable
        for file in glob.glob('data' + os.sep + '**', recursive=True):
            os.chmod(file, S_IWUSR | S_IREAD)

        if os.path.exists(SYNC_OUTPUT):
            shutil.rmtree(SYNC_OUTPUT)

        if os.path.exists(SYNC_INPUT):
            shutil.rmtree(SYNC_INPUT)

        if not os.path.exists(SYNC_OUTPUT):
            os.mkdir(SYNC_OUTPUT)

        if not os.path.exists(SYNC_INPUT):
            os.mkdir(SYNC_INPUT)

        self.__create_sub_dir('sub_folder')
        self.__create_file('test_file1.txt', 'some test text')
        self.__create_file('test_file3.txt', '...')
        self.__create_file('sub_folder/test_file2.txt', 'sub folder test file')

    def doCleanups(self):
        self.tearDown()

    def test_basic_synchronization_without_separator(self):
        self.__print_debug("before synchronization")

        synchronizer = Synchronizer()
        with self.assertLogs('synchronizer.dir_sync.Synchronizer', level='INFO') as cm:
            synchronizer.synchronize(SYNC_INPUT, SYNC_OUTPUT)
            self.assertEqual(5, len(cm.records))
            self.assertEqual(f"Started with synchronization of {SYNC_INPUT} to {SYNC_OUTPUT}",
                             cm.records[0].getMessage())
            self.assert_log_missing_directory(cm.records[1].getMessage(), 'sub_folder')
            self.assert_log_missing_file(cm.records[2].getMessage(), 'sub_folder', 'test_file2.txt')
            self.assert_log_missing_file(cm.records[3].getMessage(), 'test_file1.txt')
            self.assert_log_missing_file(cm.records[4].getMessage(), 'test_file3.txt')

        self.__compare_source_and_target()

    def test_basic_synchronization_with_separator(self):
        self.__print_debug("before synchronization")

        synchronizer = Synchronizer()
        with self.assertLogs('synchronizer.dir_sync.Synchronizer', level='INFO') as cm:
            synchronizer.synchronize(SYNC_INPUT + os.sep, SYNC_OUTPUT + os.sep)

            self.assertEqual(5, len(cm.records))
            self.assertEqual(f"Started with synchronization of {SYNC_INPUT + os.sep} to {SYNC_OUTPUT + os.sep}",
                             cm.records[0].getMessage())
            self.assert_log_missing_directory(cm.records[1].getMessage(), 'sub_folder')
            self.assert_log_missing_file(cm.records[2].getMessage(), 'sub_folder', 'test_file2.txt')
            self.assert_log_missing_file(cm.records[3].getMessage(), 'test_file1.txt')
            self.assert_log_missing_file(cm.records[4].getMessage(), 'test_file3.txt')

        self.__compare_source_and_target()

    def test_change_in_file(self):
        synchronizer = Synchronizer()
        synchronizer.synchronize(SYNC_INPUT, SYNC_OUTPUT)

        # different file size
        self.__create_file('test_file1.txt', 'some test text and longer text')
        # different file modification time
        self.__create_file('test_file3.txt', '+++')
        # new file
        self.__create_file('test_file_new.txt', 'newly created file')
        self.__create_file('sub_folder/test_sub_file_new.txt', 'newly created sub file')

        self.__print_debug("before synchronization")

        with self.assertLogs('synchronizer.dir_sync.Synchronizer', level='INFO') as cm:
            synchronizer.synchronize(SYNC_INPUT, SYNC_OUTPUT)

            self.assertEqual(5, len(cm.records), 'Expected different number of log entries')
            self.assertEqual(f"Started with synchronization of {SYNC_INPUT} to {SYNC_OUTPUT}",
                             cm.records[0].getMessage())
            self.assert_log_missing_file(cm.records[1].getMessage(), 'sub_folder', 'test_sub_file_new.txt')
            self.assert_log_changed_meta(cm.records[2].getMessage(), 'test_file1.txt')
            self.assert_log_changed_meta(cm.records[3].getMessage(), 'test_file3.txt')
            self.assert_log_missing_file(cm.records[4].getMessage(), 'test_file_new.txt')

        self.__compare_source_and_target()

    def test_change_in_directory(self):
        synchronizer = Synchronizer()
        synchronizer.synchronize(SYNC_INPUT, SYNC_OUTPUT)

        self.__create_sub_dir('new_sub_directory')
        self.__create_file('new_sub_directory/new_file_in_sub_directory.txt', '.,.,.,.,.,')

        os.renames(SYNC_INPUT + os.sep + 'sub_folder', SYNC_INPUT + os.sep + 'something_different')

        self.__print_debug("before synchronization")

        with self.assertLogs('synchronizer.dir_sync.Synchronizer', level='INFO') as cm:
            synchronizer.synchronize(SYNC_INPUT, SYNC_OUTPUT)

            self.assertEqual(6, len(cm.records), 'Expected different number of log entries')
            self.assertEqual(f"Started with synchronization of {SYNC_INPUT} to {SYNC_OUTPUT}",
                             cm.records[0].getMessage())
            self.assert_log_missing_directory(cm.records[1].getMessage(), 'new_sub_directory')
            self.assert_log_missing_file(cm.records[2].getMessage(), 'new_sub_directory', 'new_file_in_sub_directory.txt')
            self.assert_log_missing_directory(cm.records[3].getMessage(), 'something_different')
            self.assert_log_missing_file(cm.records[4].getMessage(), 'something_different', 'test_file2.txt')

        self.__compare_source_and_target()

    def test_change_in_file_mod(self):
        synchronizer = Synchronizer()
        synchronizer.synchronize(SYNC_INPUT, SYNC_OUTPUT)

        os.chmod(SYNC_INPUT + os.sep + 'test_file1.txt', S_IREAD|S_IRGRP|S_IROTH)

        with self.assertLogs('synchronizer.dir_sync.Synchronizer', level='INFO') as cm:
            synchronizer.synchronize(SYNC_INPUT, SYNC_OUTPUT)

            self.assertEqual(2, len(cm.records), 'Expected different number of log entries')
            self.assertEqual(f"Started with synchronization of {SYNC_INPUT} to {SYNC_OUTPUT}",
                             cm.records[0].getMessage())
            self.assert_log_changed_mode(cm.records[1].getMessage(), 'test_file1.txt')

        self.__compare_source_and_target()

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

        with open(input_f, 'r') as input_file, open(output_f, 'r') as output_file:
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
                              ' original -> \d*, replica -> \d*')

    @staticmethod
    def __create_file(file: str, content: str):
        f = open(SYNC_INPUT + os.sep + file, "w")
        f.write(content)
        f.close()

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
