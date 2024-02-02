from datetime import timedelta

class Config:
    """
    Class that contains static constants.
    """
    HOSTNAME = 'localhost'
    PORT = 6002

    OFFLINE_TIMEOUT = timedelta(seconds=30)
