from os import path, getcwd

from xss_receiver import cache


class CachedConfig:
    def __init__(self):
        self.inited = False

        config = {}
        with open(path.join(getcwd(), path.dirname(__file__), 'Config.py')) as config_file:
            exec(config_file.read(), None, config)

        self.ADMIN_PASSWORD = config['ADMIN_PASSWORD']
        self.RECV_MAIL_ADDR = config['RECV_MAIL_ADDR']
        self.TEMP_FILE_SAVE = config['TEMP_FILE_SAVE']

        self.inited = True

    def chage_config(self, key, val):
        config = {}
        with open(path.join(getcwd(), path.dirname(__file__), 'Config.py')) as config_file:
            exec(config_file.read(), None, config)

        config[key] = val

        with open(path.join(getcwd(), path.dirname(__file__), 'Config.py'), 'w') as config_file:
            for key in config:
                config_file.write(f"{key} = {config[key].__repr__()}")
                config_file.write('\n')

    @property
    def ADMIN_PASSWORD(self):
        return cache.get('ADMIN_PASSWORD')

    @ADMIN_PASSWORD.setter
    def ADMIN_PASSWORD(self, val):
        cache.set('ADMIN_PASSWORD', val)
        if self.inited:
            self.chage_config('ADMIN_PASSWORD', val)

    @property
    def TEMP_FILE_SAVE(self):
        return cache.get('TEMP_FILE_SAVE')

    @TEMP_FILE_SAVE.setter
    def TEMP_FILE_SAVE(self, val):
        cache.set('TEMP_FILE_SAVE', val)
        if self.inited:
            self.chage_config('TEMP_FILE_SAVE', val)

    @property
    def RECV_MAIL_ADDR(self):
        return cache.get('RECV_MAIL_ADDR')

    @RECV_MAIL_ADDR.setter
    def RECV_MAIL_ADDR(self, val):
        cache.set('RECV_MAIL_ADDR', val)
        if self.inited:
            self.chage_config('RECV_MAIL_ADDR', val)
