from datetime import timedelta

class Config:
    """
    Class that contains static constants.
    """
    # hostname and port for the flask application
    HOSTNAME = '0.0.0.0'
    PORT = 5000

    # server ip to deploy for raspberry installation
    SERVER_IP = '127.0.0.1'

    OFFLINE_TIMEOUT = timedelta(seconds=30)
