import datetime
import json
import decimal
from flask import Blueprint, render_template, g, Response, url_for

from sql_errors import catch_sql_errors
from schema import DataTable, metadata
from menu import add_menu
from dtables.dtorm import DTable, DTColumn
from dtables.funs import vhandler

reports = Blueprint('reports', __name__, template_folder='templates')


def sg(obj):
    if isinstance(obj, datetime.date):
        return str(obj)
    elif isinstance(obj, decimal.Decimal):
        return str(obj)
    else:
        raise TypeError("Unserializable object {} of type {}".format(obj, type(obj)))


class SensorsDTable(DTable):
    data__timestamp = DTColumn()
    data__probe = DTColumn()
    data__value = DTColumn()

    @classmethod
    def dt_item_id(self, item):
        return item.data__timestamp.strftime("%Y%m%d:%H%m%S-") + str(item.data__probe)


@reports.route('/values_data')
def values_data():
    qry = g.session.query(DataTable)

    results = vhandler(qry, metadata.tables, dtable=SensorsDTable)
    return Response(json.dumps(results, default=sg), mimetype='application/json')


@add_menu('Reports', 'Values', 'values', reports)
@reports.route('/values')
@catch_sql_errors('login')
def values():
    return render_template('generic_report.html',
                           dtable=SensorsDTable,
                           get_data=url_for('reports.values_data', what=None),
                           title='Sensors')
