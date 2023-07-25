# dir_sync - Directory synchronization
Directory synchronization is small script which will keep backup of provided source directory to target folder.

### Minimal requirements
**Python in version 3.11+** has to be used due to usage of glob with inclusion of hidden files.

### Usage
Check of change is done by comparison folder and file structure, file size, modification date, file mode and ownership of files.

Synchronization should be run as Python script by running **run.py** from root folder with desired parameters.
You can always use run.py -h to get list of possible parameters.

Immediate run can be used together with e.g. cron to schedule synchronization directly on Linux  

#### Mandatory parameters

- -i input folder
- -o output folder

#### Optional parameters

- -l where to store logs (default is in log_conf.yaml under handlers -> file -> filename)
- -t time interval in format {time value}{time unit} e.g. 5s -> 5 seconds. If not provided synchronization is run straight away

### Possible improvements and weaknesses

- available space of storage on target folder is not checked before copy of the file which was changed
- permissions of file and directories are not checked before copy of the file. Script expect that user has full permission to the input folder
- I developed it and run it only on Windows machine. Linux and possibly MacOS should be also tested
- only unit/component tests are provided. It will be good to also write integration tests on environment where we can control use permission to cover additional cases
- schedule module is used only partly. It supports more options than only to run it in fixed time relative interval
- error handling is not covering all possibilities e.g. what to do if synchronization on some file/directory fails? Now it will terminate whole script. It would be possibly good to just log the error and continue with synchronization
- it would make sense to allow user to provide possibility to run first synchronization with delay and then continue with fixed interval
- there can be problems when files are changing during synchronization in input folder
- it would be good to detect for example move / rename of folders, so it will not be deleted and recreated under new name / location but renamed / moved
- script is not ready to run in parallel so the time interval should be wide enough that it can finish synchronization before next run
- directories are just created in case that they don't exist but there is no check about permissions and no metadata are transferred
- symlinks are not supported
- there is no check that source and target folders are not the same which would make run of script unnecessary
