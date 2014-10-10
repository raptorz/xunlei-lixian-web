# -*- coding: utf-8 -*-
"""
    start web server
    ~~~~~~~~~~~~~~~~
    powered by bottle.py

    :copyright: 20130118 by raptor.zh@gmail.com.
    revision:   20130525 bottle.py
                20141010 bottle 0.12+
"""
import sys
import os
import bottle
from bottle import Bottle, run

from model import get_fullname
from apimain import app

import logging

logger = logging.getLogger(__name__)

application = Bottle()
v = bottle.__version__.split(".")
if v[0]=="0" and v[1]<"12":
    application.mount(app, "/xunlei")
else:
    application.mount("/xunlei", app)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    # dev run
    import subprocess
    svc = subprocess.Popen([sys.executable, get_fullname("service.py")], shell=False)
    os.chdir(get_fullname(""))
    run(application, host="0.0.0.0", port=8180, debug=True)
    svc.terminate()
