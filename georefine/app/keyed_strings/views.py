from georefine.app import app
from flask import Blueprint, request, jsonify
from georefine.app import db
from georefine.app.keyed_strings.models import KeyedString

import hashlib

bp = Blueprint('keyed_strings', __name__, url_prefix='/ks')

@bp.route('/getKey/', methods=['POST'])
def getKey():
    s = request.form.get('s', '')
    key = hashlib.md5(s).hexdigest()
    ks = db.session.query(KeyedString).filter(KeyedString.key == key).first()
    if not ks:
        print "saving"
        ks = KeyedString(key = key, s = s)
        db.session.add(ks)
        db.session.commit()
    return jsonify(key=key)

@bp.route('/getString/<key>', methods=['GET'])
def getString(key):
    s = key
    ks = db.session.query(KeyedString).filter(KeyedString.key == key).first()
    return jsonify(s=ks.s)


