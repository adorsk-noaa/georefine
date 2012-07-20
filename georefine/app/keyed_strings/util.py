from georefine.app import db
from georefine.app.keyed_strings.models import KeyedString
import hashlib

def getKey(s):
    key = hashlib.md5(s).hexdigest()
    ks = db.session.query(KeyedString).filter(KeyedString.key == key).first()
    if not ks:
        print "saving"
        ks = KeyedString(key = key, s = s)
        db.session.add(ks)
        db.session.commit()
    return key

def getString(key):
    ks = db.session.query(KeyedString).filter(KeyedString.key == key).first()
    return ks.s
