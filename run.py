import logging.config

import yaml

from synchronizer.dir_sync import Synchronizer

if __name__ == '__main__':
    with open('log_conf.yaml', mode='rt', encoding='utf-8') as file:
        conf = yaml.safe_load(file)
        logging.config.dictConfig(conf)

    sync = Synchronizer()
    sync.synchronize(r'C:\Users\franc\PycharmProjects\dir_sync\tttt', '.')
