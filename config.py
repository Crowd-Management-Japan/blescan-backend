from datetime import timedelta

class Config:
    """
    Class that contains static constants.
    """
    # hostname and port for the flask application
    HOSTNAME = 'localhost'
    PORT = 6002

    # server ip to deploy for raspberry installation
    SERVER_IP = '127.0.0.1'

    OFFLINE_TIMEOUT = timedelta(seconds=30)

    # folder where to store uploaded raspi logs
    RASPI_LOG_FOLDER = 'res/raspi_logs/'