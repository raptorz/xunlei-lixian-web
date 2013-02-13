# -*- coding: utf-8 -*-
"""
    download service
    ~~~~~~~~~~~~~~~~

    :copyright: 20130209 by raptor.zh@gmail.com.
"""
import sys
import subprocess
import time
import web

from apiprovider import get_fullname

import logging

logger = logging.getLogger(__name__)


def get_config(dbconn, name):
    r = dbconn.select('config', where='key=$key', vars={'key':name}).list()
    if len(r) == 0:
        return ""
    return r[0]['value']


def download_all(dbconn):
    tasks = dbconn.select("task", where="state in ('waiting', 'working')")
    for task in tasks:
        subprocess.call([sys.executable, get_fullname("lixian", "lixian_cli.py"), "config", "username", get_config(dbconn, "username")], shell=False)
        subprocess.call([sys.executable, get_fullname("lixian", "lixian_cli.py"), "config", "password", get_config(dbconn, "userpass")], shell=False)
        dbconn.update("task", where="id=$id", vars={"id":task["id"]}, state="working")
        arg = (task['state'] == 'working') and "--continue" or ""
        retcode = subprocess.call([sys.executable, get_fullname("lixian", "lixian_cli.py"), "download", str(task['id']), arg], shell=False)
        state = (retcode == 0) and 'downloaded' or 'error'
        dbconn.update("task", where="id=$id", vars={"id":task["id"]}, state=state)


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)
    db = get_fullname("xllxweb.dat")
    dbconn = web.database(dbn='sqlite', db=db)
    while True:
        download_all(dbconn)
        time.sleep(30)
