import datetime
from flask import Blueprint, g, request, jsonify

from schema import DataTable, Sensors

receiver = Blueprint('receiver', __name__)
receiver.stable = dict()

@receiver.route('/esp_probe', methods=['POST'])
def esp_probe():
    if not receiver.stable:
        for ii in g.session.query(Sensors.id, Sensors.label):
            receiver.stable[ii.label] = ii.id
    print request.json
    for kk, vv in request.json.items():
        g.session.add(DataTable(probe=receiver.stable[kk], value=vv, timestamp=datetime.datetime.now()))
    return jsonify(result="OK")
