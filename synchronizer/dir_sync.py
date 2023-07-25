"""
Directory synchronization implementation.

Only local disk synchronization is supported right now.
"""
import glob
import logging
import os
from os import stat_result
import shutil

log = logging.getLogger('synchronizer.dir_sync.Synchronizer')


class SynchronizerException(Exception):
    pass


class Synchronizer:
    """
    Handle directory synchronization from provided input_dir to output_dir.
    Directories must be from same system.

    File and directory presence between input and output directory is checked together with file size, modification time
    file mode and owners.
    """
    def synchronize(self, input_dir: str, output_dir: str):
        log.info("Started with synchronization of %s to %s", input_dir, output_dir)
        input_dir = self.__fix_directory_postfix(input_dir)
        output_dir = self.__fix_directory_postfix(output_dir)

        if not os.path.exists(input_dir) or not os.path.isdir(input_dir):
            raise SynchronizerException("Wrong input directory was provided")

        if not os.path.exists(output_dir) or not os.path.isdir(output_dir):
            raise SynchronizerException("Wrong output directory was provided")

        iterator = glob.iglob(input_dir + "**", recursive=True, include_hidden=True)
        for file in iterator:
            relative_path = self.__relative_path(file, input_dir)
            if not relative_path:
                continue
            log.debug("Processing item: %s", relative_path)
            target = os.path.join(output_dir, relative_path)

            self.__create_directory_if_missing(file, target)
            self.__create_file_if_missing(file, target)
            self.__update_file_if_needed(file, target)

        self.__cleanup_replica(input_dir, output_dir)

    @staticmethod
    def __fix_directory_postfix(input_dir: str) -> str:
        """
        add directory separator to the end of provided directory if it is not already there
        :param input_dir: path to directory
        :return: provided directory with ending folder separator
        """
        if input_dir[-1] != '\\' and input_dir[-1] != '/':
            return input_dir + os.sep
        return input_dir

    @staticmethod
    def __relative_path(input_dir: str, base_dir: str):
        return input_dir.replace(base_dir, '')

    @staticmethod
    def __create_directory_if_missing(source: str, target: str):
        if os.path.isdir(source) and not os.path.isdir(target):
            log.info("Creating new directory '%s' in replica", target)
            os.mkdir(target)

    @staticmethod
    def __create_file_if_missing(source: str, target: str):
        if os.path.isfile(source) and not os.path.isfile(target):
            log.info("Copying missing file '%s' to replica", target)
            shutil.copy2(source, target)

    def __cleanup_replica(self, input_dir: str, output_dir: str):
        iterator = glob.iglob(output_dir + "**", recursive=True, include_hidden=True)
        for file in iterator:
            relative_path = self.__relative_path(file, output_dir)
            target = os.path.join(input_dir, relative_path)
            if not os.path.exists(target) and os.path.isdir(file):
                log.info("Removing no longer existing directory '%s' from replica", file)
                shutil.rmtree(file)
            elif not os.path.exists(target) and os.path.isfile(file):
                log.info("Removing no longer existing file '%s' from replica", file)
                os.remove(file)

    def __update_file_if_needed(self, source: str, target: str):
        if os.path.isfile(source):
            source_stats = os.stat(source)
            target_stats = os.stat(target)

            if source_stats.st_size != target_stats.st_size or source_stats.st_mtime != target_stats.st_mtime:
                log.info("Updating file with changed metadata '%s': original -> %s, replica -> %s",
                         target, self.__get_stats_info(source_stats), self.__get_stats_info(target_stats))
                shutil.copy2(source, target)

            if source_stats.st_mode != target_stats.st_mode:
                log.info("Updating file mode '%s': original -> %s, replica -> %s", target, source_stats.st_mode,
                         target_stats.st_mode)
                os.chmod(target, source_stats.st_mode)

            if source_stats.st_uid != target_stats.st_uid or source_stats.st_gid != target_stats.st_gid:
                log.info("Updating file owners of '%s': original -> %s, replica -> %s", target,
                         self.__get_owners(source_stats), self.__get_owners(target_stats))
                os.chown(target, source_stats.st_uid, source_stats.st_gid)

    @staticmethod
    def __get_stats_info(stats: stat_result) -> dict:
        return {'size': stats.st_size, 'modified': stats.st_mtime}

    @staticmethod
    def __get_owners(stats: stat_result) -> dict:
        return {'owner': stats.st_uid, 'group': stats.st_gid}
