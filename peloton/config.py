import logging
import os
import pathlib

def get_logger():
    """ To change log level from calling code, use something like
        logging.getLogger("peloton").setLevel(logging.DEBUG)
    """
    logger = logging.getLogger("peloton")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

class Config:

    def __init__(self):
        self.SHOW_WARNINGS = False

        import configparser
        parser = configparser.ConfigParser()
        conf_path = os.environ.get("PELOTON_CONFIG", "~/.config/peloton")
        parser.read(os.path.expanduser(conf_path))

        try:
            # Mandatory credentials
            self.PELOTON_USERNAME = os.environ.get("PELOTON_USERNAME") \
                or parser.get("peloton", "username")
            self.PELOTON_PASSWORD = os.environ.get("PELOTON_PASSWORD") \
                or parser.get("peloton", "password")

        except (configparser.NoOptionError, configparser.NoSectionError) as e:
            get_logger().warning(
                "No `username` or `password` found in section `peloton` "
                "in ~/.config/peloton\n"
                "Please ensure you specify one prior to utilizing the API\n")

            # Additional option to show or hide warnings
        try:
            ignore_warnings = parser.getboolean("peloton", "ignore_warnings")
            self.SHOW_WARNINGS = False if ignore_warnings else True

        except:
            self.SHOW_WARNINGS = False

        if self.SHOW_WARNINGS:
            get_logger().setLevel(logging.WARNING)
        else:
            get_logger().setLevel(logging.ERROR)

        # Whether or not to verify SSL connections (defaults to True)
        try:
            self.SSL_VERIFY = parser.getboolean("peloton", "ssl_verify")
        except:
            self.SSL_VERIFY = True

        # If set, we'll use this cert to verify against. Useful when you're
        # stuck behind SSL MITM
        try:
            self.SSL_CERT = parser.get("peloton", "ssl_cert")
        except:
            self.SSL_CERT = None

        # If set, we'll cache the JSON results from API calls in this directory.
        # For people with a lot of workouts, this lessons the load on the server
        # significantly to use cached results rather than hitting the server all the time
        try:
            self.DATA_CACHE_DIR = pathlib.Path(parser.get("peloton", "data_cache_dir"))
        except:
            self.DATA_CACHE_DIR = None

        if self.SHOW_WARNINGS:
            get_logger().setLevel(logging.WARNING)
        else:
            get_logger().setLevel(logging.ERROR)
