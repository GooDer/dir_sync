import glob
import logging
import os

log = logging.getLogger('synchronizer.dir_sync.Synchronizer')


class Synchronizer:
    def synchronize(self, input_dir: str, output_dir: str):
        log.info("Started with synchronization of %s to %s", input_dir, output_dir)
        fixed_in_dir = self.__fix_directory_postfix(input_dir)

        iterator = glob.iglob(fixed_in_dir + "**", recursive=True)
        for file in iterator:
            relative_path = self.__relative_path(file, fixed_in_dir)
            if not relative_path:
                continue
            log.debug("Processing item: %s", relative_path)

    @staticmethod
    def __fix_directory_postfix(input_dir: str):
        if input_dir[-1] != '\\' and input_dir[-1] != '/':
            return input_dir + os.sep
        return input_dir

    @staticmethod
    def __relative_path(input_dir: str, base_dir: str):
        return input_dir.replace(base_dir, '')
