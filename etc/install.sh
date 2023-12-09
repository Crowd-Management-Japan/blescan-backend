# install the service file and activate it

# the working directory should be blescan-backen (one level above)

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

sudo cp etc/blescan-backend.service /lib/systemd/system/

sudo systemctl enable blescan-backend.service
sudo systemctl start blescan-backend.service