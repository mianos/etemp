import datetime
from dateutil import tz
import calendar

from flask import Blueprint, render_template, g, jsonify, request
from sqlalchemy import func, and_, inspect, types

from schema import DataTable, Sensors
from menu import add_menu
from jsonp import support_jsonp

graphs = Blueprint('graphs', __name__, template_folder='templates')


def utc1ktztolocal(onekts):
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()
    utc = datetime.datetime.fromtimestamp(float(onekts) / 1000.0).replace(tzinfo=from_zone)
    out = utc.astimezone(to_zone).replace(tzinfo=None)
    return out


def localtoutc1k(tt):
    from_zone = tz.tzlocal()
    to_zone = tz.tzutc()
    local = tt.replace(tzinfo=from_zone)
    out = local.astimezone(to_zone).replace(tzinfo=None)
    return calendar.timegm(out.timetuple()) * 1000


aft = {'sfun_avg': [func.avg],
       'sfun_min_max': [func.max, func.min]}


# @series_cache.cache_on_arguments(namespace='json_data')
def sensord(id, start, end, aft_name):
    functions = aft[aft_name]
    table = inspect(DataTable).mapped_table

    fields = list()
    for agg_func in functions:
        agg_func_name = str(agg_func()).replace('()', '')
        fields.append(func.cast(agg_func(DataTable.value), types.Integer).label(agg_func_name))

    per_seconds = (end - start).total_seconds() / 100
    ots = func.to_timestamp(func.round(func.extract('epoch', DataTable.timestamp) / per_seconds) * per_seconds).label('timestamp')

    if id == 0:
        qry = g.session.query(ots, *fields) \
                       .filter(DataTable.probe == 1)    # TODO: get probe 1
    else:
        qry = g.session.query(ots, *fields) \
                       .filter(DataTable.probe == id)

    qry = qry.filter(table.c.timestamp >= start, table.c.timestamp <= end) \
             .group_by(ots) \
             .order_by(ots)
    return qry


@graphs.route('/jdata/<int:id>')
@support_jsonp
def jdata(id=None):
    start = utc1ktztolocal(request.args.get('start'))
    end = utc1ktztolocal(request.args.get('end'))
    sensor = g.session.query(Sensors).filter(Sensors.id == id).first()
    if sensor.sclass == 'humidity':
        qry = sensord(id, start, end, 'sfun_avg')
        return jsonify(data=[dict(x=localtoutc1k(ii.timestamp), y=ii.avg) for ii in qry])
    elif sensor.sclass == 'light':
        qry = sensord(id, start, end, 'sfun_avg')
        return jsonify(data=[dict(x=localtoutc1k(ii.timestamp), y=ii.avg) for ii in qry])
    else:
        qry = sensord(id, start, end, 'sfun_min_max')
        return jsonify(data=[dict(x=localtoutc1k(ii.timestamp), low=ii.min, high=ii.max) for ii in qry])


@graphs.route('/jsond/<int:id>')
def jsond(id=None):
    # Get the min and max only for the sensors that are displayed
    qry = g.session.query(func.min(DataTable.timestamp), func.max(DataTable.timestamp)) \
                   .join(Sensors, and_(Sensors.id == DataTable.probe, Sensors.display == True))
    start, end = qry.first()
    if id == 0:
        # navigation
        qry = sensord(id, start, end, 'sfun_avg')
        return jsonify(data=[dict(x=localtoutc1k(ii.timestamp), y=ii.avg) for ii in qry])
    else:
        sensor = g.session.query(Sensors).filter(Sensors.id == id).first()
        if sensor.sclass == 'humidity':
            qry = sensord(id, start, end, 'sfun_avg')
            return jsonify(data=[dict(x=localtoutc1k(ii.timestamp), y=ii.avg) for ii in qry])
        elif sensor.sclass == 'light':
            qry = sensord(id, start, end, 'sfun_avg')
            return jsonify(data=[dict(x=localtoutc1k(ii.timestamp), y=ii.avg) for ii in qry])
        else:
            qry = sensord(id, start, end, 'sfun_min_max')
            return jsonify(data=[dict(x=localtoutc1k(ii.timestamp), low=ii.min, high=ii.max) for ii in qry])


@add_menu('Graphics', 'Temps', 'temps', graphs)
@graphs.route('/temps')
def temps():
    sensors = g.session.query(Sensors).filter(Sensors.display == True).order_by(Sensors.id)
    return render_template('graph.html', sensors=sensors)
