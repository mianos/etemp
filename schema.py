#!/usr/bin/env python
import datetime

import ConfigParser
import argparse

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import types, Column, ForeignKey, create_engine

dbase = declarative_base()
metadata = dbase.metadata

class Sensors(dbase):
    __tablename__ = 'sensors'
    id = Column(types.Integer, primary_key=True)
    label = Column(types.String(length=40))
    name = Column(types.String(length=128), unique=True)
    sclass = Column(types.String(length=20))
    display = Column(types.Boolean)


class DataTable(dbase):
    __tablename__ = 'data'
    timestamp = Column(types.DateTime, primary_key=True, nullable=False, default=datetime.datetime.now())
    probe = Column(types.Integer, ForeignKey(Sensors.id), primary_key=True)
    value = Column(types.Integer)

    def __repr__(self):
        return "<date(%d, %d, %s)>" % (self.probe, self.value, str(self.timestamp))


if __name__ == '__main__':

    config = ConfigParser.ConfigParser()
    parser = argparse.ArgumentParser(description='check stuff and email')
    parser.add_argument("-f", "--config", dest="config", default='settings.ini', help="config file")
    parser.add_argument("-s", "--section", dest="section", default='beta', help="config file section")
    parser.add_argument("-c", "--create", dest="create", action="store_true", default=None, help="Create Tables")
    parser.add_argument("-d", "--delete", dest="delete", action="store_true", default=None, help="delete data from 'data' tables")
    parser.add_argument("-r", "--drop-all", dest="drop_all", action="store_true", default=None, help="drop all 'data' tables")
    parser.add_argument("-t", "--test-data", dest="test_data", action="store_true", default=None, help="generate test data")
    options = parser.parse_args()
    config.readfp(open(options.config))

    engine = create_engine(config.get(options.section, 'uri'))

    if options.create:
        dbase.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    if options.delete or options.drop_all:
        for table in dbase.metadata.sorted_tables:
            if table.name.find('data') == 0:
                print "deleting from", table.name
                if options.delete:
                    session.execute(table.delete())
                if options.drop_all:
                    session.execute('drop table %s' % table.name)
        session.commit()
