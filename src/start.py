# -*- coding: utf-8 -*-
"""
    start web server
    ~~~~~~~~~~~~~~~~
    powered by bottle.py

    :copyright: 20130118 by raptor.zh@gmail.com.
    revision: 20130525 bottle.py
"""
import sys
import os
from bottle import Bottle, run

from model import get_fullname
from apimain import app

import logging

logger = logging.getLogger(__name__)

application = Bottle()
application.mount(app, "/xunlei")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    # dev run
    import subprocess
    svc = subprocess.Popen([sys.executable, get_fullname("service.py")], shell=False)
    os.chdir(get_fullname(""))
    run(application, host="0.0.0.0", port=8180, debug=False)
    svc.terminate()
