# -*- coding: utf-8 -*-
"""
    download service
    ~~~~~~~~~~~~~~~~

    :copyright: 20130209 by raptor.zh@gmail.com.
"""
import sys
import subprocess
import time

from model import *

import logging

logger = logging.getLogger(__name__)


def download_all(orm):
    tasks = Task._get_incomp(orm)
    for task in tasks:
        username = Config._get_value(orm, "username")
        userpass = Config._get_value(orm, "userpass")
        if len(username) < 2 or len(userpass) < 2:
            return
        subprocess.call([sys.executable, get_fullname("lixian", "lixian_cli.py"), "config", "username", username], shell=False)
        subprocess.call([sys.executable, get_fullname("lixian", "lixian_cli.py"), "config", "password", userpass], shell=False)
        Task._update(orm, task.id, dict(state=STATE_WORKING))
        arg = (task.state == STATE_WORKING) and "--continue" or ""
        retcode = subprocess.call([sys.executable, get_fullname("lixian", "lixian_cli.py"), "download", str(task.id), arg], shell=False)
        state = (retcode == 0) and 'downloaded' or 'error'
        Task._update(orm, task.id, dict(state=state))


if __name__ == "__main__":
    from sqlalchemy.orm import scoped_session, sessionmaker
    import logging
    logging.basicConfig(level=logging.DEBUG)
    orm = scoped_session(sessionmaker(bind=engine))
    while True:
        download_all(orm)
        time.sleep(30)
