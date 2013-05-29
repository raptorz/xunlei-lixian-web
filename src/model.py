# -*- coding: utf-8 -*-
"""
    data model
    ~~~~~~~~~~~~~~~~

    sqlalchemy data model.

    :copyright: 20130423 by raptor.zh@gmail.com.
"""
import os.path

from sqlalchemy import create_engine, Column, Integer, String, Unicode
from sqlalchemy.ext.declarative import declarative_base

import logging

logger = logging.getLogger(__name__)


def get_fullname(*args):
    name = os.path.join(*args)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), name)


engine = create_engine('sqlite:///%s' % get_fullname("xllxweb.dat"))
#conf = dict(url='sqlite:///xllxweb.dat')
#engine = engine_from_config(conf)
Base = declarative_base()


STATE_COMPLETED  = "completed"
STATE_WAITING    = "waiting"
STATE_WORKING    = "working"
STATE_DOWNLOADED = "downloaded"
STATE_ERROR      = "error"


class Config(Base):
    __tablename__ = "config"

    key   = Column(String(100), primary_key=True)
    value = Column(String(100))

    @staticmethod
    def _get(orm, key):
        return orm.query(Config).filter(Config.key==key).first()

    @staticmethod
    def _get_value(orm, key):
        r = Config._get(orm, key)
        return r and r.value or None 

    @staticmethod
    def _put(orm, key, value):
        r = Config._get(orm, key)
        if r:
            r.value = value
        else:
            r = Config(key=key, value=value)
            orm.add(r)
        orm.commit()


class Task(Base):
    __tablename__ = "task"

    id    = Column(String(100), primary_key=True)
    name  = Column(Unicode(200), nullable=False)
    state = Column(String(100))

    @staticmethod
    def _get_all(orm):
        return orm.query(Task).all()

    @staticmethod
    def _get_incomp(orm):
        return orm.query(Task).filter(Task.state.in_([STATE_WAITING, STATE_WORKING])).all()

    @staticmethod
    def _get(orm, id):
        return orm.query(Task).filter(Task.id==id).first()

    @staticmethod
    def _insert(orm, kwargs):
        r = Task(**kwargs)
        orm.add(r)
        orm.commit()
        return r

    @staticmethod
    def _update(orm, id, kwargs):
        r = Task._get(orm, id)
        for k,v in kwargs.iteritems():
            setattr(r, k, v)
        orm.commit()
        return r

    @staticmethod
    def _detete(orm, id):
        r = Task._get(orm, id)
        orm.delete(r)
        orm.commit()


metadata = Base.metadata


if __name__ == "__main__":
    metadata.create_all(engine)
