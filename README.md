# blescan-backend
This backend is used in combination with the [blescan](https://github.com/Crowd-Management-Japan/blescan/) application.
Blescan is a raspberry pi software that counts surrounding ble devices. 
When using it with multiple raspi's, it is much work to set them up properly and collect the data afterwards.
For this specific case, this backend is created and used.  
It provides a small API (and web interface) that the blescan software can connect to to update its configuration and send live data to.
The data will be saved in a sqlalchemy database to be downloaded any time. It is also easy to delete the data before an experiment starts.

Keep in mind that this backend is meant to be used privately!  
That is also the reason why there are no real safety implementations.
The data is not critical and even if it is deleted, the original data is on the raspberries itself.
It is more like a live-status of the currently running experiment!

# Installation
For a full installation on a linux server (inclusive service) run `etc/install.sh`.

For a more developing state follow these instructions:

- clone the repository and navigate in it.
- (optional) create a python environment `python -m venv .venv` and `source .venv/bin/activate`
- Install requirements with `pip install -r requirements.txt`
- run `python blescan.py` to start the backend


# Contribution
Feel free to contribute by opening and resolving issues and opening pull requests.
