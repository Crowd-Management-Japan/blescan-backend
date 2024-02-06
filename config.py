from datetime import timedelta

class Config:
    """
    Class that contains static constants.
    """
    # hostname and port for the flask application
    HOSTNAME = '0.0.0.0'
    PORT = 5000

    # server ip to deploy for raspberry installation
    SERVER_IP = '194.195.92.252'

    OFFLINE_TIMEOUT = timedelta(seconds=30)
