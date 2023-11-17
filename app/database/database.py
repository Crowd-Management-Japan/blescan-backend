
from app import db

class Device(db.Model):
    id = db.Column(db. Integer, primary_key=True)
    last_updated = db.Column(db.String(20))

    def __repr__(self):
        return 'Device %r' % self.last_updated