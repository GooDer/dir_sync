"""
Main runnable script with input parameters from command line
"""
import argparse
import logging.config

import yaml

from synchronizer.dir_sync import Synchronizer
from job.job_runner import  JobRunner

if __name__ == '__main__':
    argParser = argparse.ArgumentParser()
    argParser.add_argument("-i", "--input_dir", help="source directory which will be synchronized to replica",
                           required=True)
    argParser.add_argument("-o", "--output_dir", help="output directory which will be synchronized from source folder",
                           required=True)
    argParser.add_argument("-l", "--log_output", help="where logs will be stored")
    argParser.add_argument("-t", "--time_interval", help="""
        provide time interval in which the synchronization should take a place. Use number with unit postfix as follows:
        5s = 5 seconds,
        10m = 10 minutes,
        4h = 4 hours,
        2d = 2 days
        """)

    args = argParser.parse_args()
    print(f'args={args}')

    with open('log_conf.yaml', mode='rt', encoding='utf-8') as file:
        conf = yaml.safe_load(file)
        if args.log_output:
            conf['handlers']['file']['filename'] = args.log_output

        logging.config.dictConfig(conf)

    if not args.time_interval:
        sync = Synchronizer()
        sync.synchronize(args.input_dir, args.output_dir)
    else:
        runner = JobRunner(args.input_dir, args.output_dir, args.time_interval)
        runner.run_job()
        logging.info('Synchronization finished')
