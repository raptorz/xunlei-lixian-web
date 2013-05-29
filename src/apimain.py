# -*- coding: utf-8 -*-
"""
    start web server
    ~~~~~~~~~~~~~~~~
    powered by bottle.py

    :copyright: 20130118 by raptor.zh@gmail.com.
    revision: 20130525 bottle.py
"""
import bottle

try:
    import json
except ImportError:
    import simplejson as json

from model import *
from common import error_exc, DataRow
from apiprovider import WebInternalError, get_plugin, get_client

from lixian.lixian import XunleiClient

import logging

logger = logging.getLogger(__name__)

class WebUnauthorizedError(bottle.HTTPError):
    def __init__(self):
        super(WebUnauthorizedError, self).__init__(401, "Unauthorized!")


class WebInternalError(bottle.HTTPError):
    def __init__(self, msg):
        super(WebInternalError, self).HTTPError.__init__(500, msg or "Internal error!")


def get_plugin():
    return bottle.ext.sqlalchemy.Plugin(engine, metadata, keyword='orm')


def auth_check(r):
    if not r:
        raise WebUnauthorizedError
    return r


def get_client(orm):
    try:
        username = Config._get_value(orm, 'username')
        userpass = auth_check(Config._get_value(orm, 'userpass'))
        client = XunleiClient(username, userpass)
        return client
    except WebUnauthorizedError:
        raise
    except:
        logger.error(error_exc())
        raise WebUnauthorizedError


app = bottle.Bottle()
app.install(get_plugin())


@app.get("/static/<filename:path>")
def static(filename):
    return bottle.static_file(filename, root=get_fullname("static"))


@app.get("/")
def index():
    bottle.redirect("static/index.html")


@app.post("/login")
def login(orm):
    try:
        for k,v in bottle.request.json.iteritems():
            if k in ['username', 'userpass'] and v != "":
                Config._put(orm, k, v)
    except:
        error_exc()
        raise
    get_client(orm)
    return ""


@app.get("/task")
def task_list(orm):
    remote_tasks = get_client(orm).read_tasks()
    working_tasks = list(Task._get_all(orm))
    working_index = {}
    [working_index.__setitem__(t.id, t) for t in working_tasks]
    result = []
    for task in remote_tasks:
        state = task['status_text']
        tid = int(task['id'])
        if tid in working_index.keys():
            state = working_index[tid].state
        result.append(DataRow(dict(id=task['id'], sn=task["#"], name=task['name'],
            size="{:,}".format(int(task['size'])), state=state)))
    return json.dumps(result)


@app.get("/task/<id:int>")
def task_item(orm, id):
    return DataRow(Task._get(orm, id))


@app.put("/task/<id:int>")
def task_update(orm, id):
    kwargs = bottle.request.json
    task = Task._get(orm, id)
    if task:
        if task['state'] == STATE_WORKING and kwargs['state'] == STATE_COMPLETED:
            Task._delete(orm, id)
        elif task['state'] == STATE_ERROR and kwargs['state'] == STATE_WORKING:
            Task._update(orm, id, dict(state=kwargs['state']))
        else:
            raise WebInternalError("Invalid operation!")
    else:
        if kwargs['state'] == STATE_WAITING:
            Task._insert(orm, dict(id=id, name=kwargs['name'], state=kwargs['state']))
        else:
            raise WebInternalError("Invalid operation!")
    return ""


@app.delete("/task/<id:int>")
def task_delete():
    task = Task._get(orm, id)
    if task:
        if task['state'] != STATE_WORKING:
            Task._delete(orm, id)
        else:
            raise WebInternalError("Invalid operation!")
    get_client(orm).delete_task_by_id(id)
    return ""
