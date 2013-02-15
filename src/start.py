# -*- coding: utf-8 -*-
"""
    start web server
    ~~~~~~~~~~~~~~~~
    powered by web.py

    :copyright: 20130118 by raptor.zh@gmail.com.
"""
import web

web.config.debug = False

from common import error_exc, DataRow
from webcommon import WebUnauthorizedError, WebInternalError
from apiserver import RestBaseHandler, kwargs_decorator
from apiprovider import get_fullname, Provider

import logging

logger = logging.getLogger(__name__)


urls = (
        "/?"                , "Index",
        "/login/?"          , "Login",
        "/task/?"           , "Task",
        "/task/([0-9]+)/?"  , "Task",
        )

app = web.application(urls, locals())


class Index:
    def GET(self):
        raise web.seeother("static/")


class APIHandler(RestBaseHandler):
    def __init__(self):
        self._provider = Provider()


class Login(APIHandler):
    @kwargs_decorator
    def POST_(self, kwargs={}):
        trans = self._provider.dbconn.transaction()
        try:
            for k,v in kwargs.iteritems():
                if k in ['username', 'userpass'] and v != "":
                    r = self._provider.dbconn.select('config', where="key=$key", vars={"key":k}).list()
                    if len(r)==0:
                        self._provider.dbconn.insert('config', key=k, value=v)
                    else:
                        self._provider.dbconn.update('config', where="key=$key", vars={"key":k}, value=v)
            trans.commit()
        except:
            error_exc()
            trans.rollback()
            raise
        return ""


class Task(APIHandler):
    STATE_COMPLETED  = "completed"
    STATE_WAITING    = "waiting"
    STATE_WORKING    = "working"
    STATE_DOWNLOADED = "downloaded"
    STATE_ERROR      = "error"
    
    def GET_(self, rid=""):
        if rid == "":
            remote_tasks = self._provider.client.read_tasks()
            working_tasks = self._provider.dbconn.select("task").list()
            working_index = {}
            [working_index.__setitem__(t['id'], t) for t in working_tasks]
            result = []
            for task in remote_tasks:
                state = task['status_text']
                tid = int(task['id'])
                if tid in working_index.keys():
                    state = working_index[tid]['state']
                result.append(DataRow(dict(id=task['id'], sn=task["#"], name=task['name'],
                    size="{:,}".format(int(task['size'])), state=state)))
            return result
        else:
            result=self._provider.dbconn.select("task", where="id=$id", vars={'id':rid}).list()
            return result[0]

    def update_task(self, rid, kwargs):
        tasks = self._provider.dbconn.select("task", where="id=$id", vars={"id":rid}).list()
        if len(tasks) > 0:
            task = tasks[0]
            if task['state'] == self.STATE_WORKING and kwargs['state'] == self.STATE_COMPLETED:
                self._provider.dbconn.delete("task", where="id=$id", vars={"id":rid})
            elif task['state'] == self.STATE_ERROR and kwargs['state'] == self.STATE_WORKING:
                self._provider.dbconn.update("task", where="id=$id", vars={"id":rid}, state=kwargs['state'])
            else:
                raise WebInternalError("Invalid operation!")
        else:
            if kwargs['state'] == self.STATE_WAITING:
                self._provider.dbconn.insert("task", id=rid, name=kwargs['name'], state=kwargs['state'])
            else:
                raise WebInternalError("Invalid operation!")
        return ""

    @kwargs_decorator
    def POST_(self, rid="", kwargs={}):
        if rid == "":
            return "" # todo: add new task to xunlei lixian
        else:
            return self.update_task(rid, kwargs)

    @kwargs_decorator
    def PUT_(self, rid, kwargs={}):
        return self.update_task(rid, kwargs)

    def DELETE_(self, rid):
        tasks = self._provider.dbconn.select("task", where="id=$id", vars={"id":rid}).list()
        if len(tasks) > 0:
            task = tasks[0]
            if task['state'] != self.STATE_WORKING:
                self._provider.dbconn.delete("task", where="id=$id", vars={"id":rid})
            else:
                raise WebInternalError("Invalid operation!")
        self._provider.client.delete_task_by_id(rid)
        return ""


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)
    db = get_fullname("xllxweb.dat")
    dbconn = web.database(dbn='sqlite', db=db)
    sql = """create table if not exists config (
        key varchar primary key not null,
        value varchar
    )"""
    dbconn.query(sql)
    sql = """create table if not exists task (
        id integer primary key not null,
        name varchar not null,
        state varchar
    )"""
    dbconn.query(sql)
    import os
    import sys
    import subprocess
    svc = subprocess.Popen([sys.executable, get_fullname("service.py")], shell=False)
    os.chdir(get_fullname(""))
    app.run()
    svc.terminate()
