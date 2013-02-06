from georefine.app import app
from flask import Blueprint, request, jsonify
from georefine.app import db
from georefine.app.keyed_strings import util as ks_util

bp = Blueprint('keyed_strings', __name__, url_prefix='/ks')

@bp.route('/getKey/', methods=['POST'])
def getKey():
    s = request.form.get('s', '')
    key = ks_util.getKey(s)
    return jsonify(key=key)

@bp.route('/getString/<key>/', methods=['GET'])
def getString(key):
    s = ks_util.getString(key)
    return jsonify(s=s)


