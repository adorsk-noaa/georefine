from georefine.app import app
from flask import Blueprint, request, jsonify
from georefine.app import db
from georefine.app.keyed_strings.models import KeyedString

bp = Blueprint('keyed_strings', __name__, url_prefix='/ks')

@bp.route('/getKey/', methods=['POST'])
def getKey():
    s = request.form.get('s', '')
    return jsonify(key=s)

@bp.route('/getString/<key>', methods=['GET'])
def getString(key):
    s = key
    return jsonify(s=s)


