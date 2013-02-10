# -*- coding: utf-8 -*-
"""
    saprovider
    ~~~~~~~~~~~~~~~~

    sqlalchemy data provider.

    :copyright: 20130127 by raptor.zh@gmail.com.
"""
import os.path
import web
from common import error_exc
from webcommon import WebUnauthorizedError

from lixian.lixian import XunleiClient

import logging

logger = logging.getLogger(__name__)


def get_fullname(*args):
    name = os.path.join(*args)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), name)


class Provider:
    def __init__(self):
        db = get_fullname("xllxweb.dat")
        self.dbconn = web.database(dbn='sqlite', db=db)

    def __getattr__(self, name):
        if name == "client":
            try:
                client = XunleiClient(self.get_config('username'), self.get_config('userpass'))
                self.client = client
                return client
            except:
                error_exc()
                raise WebUnauthorizedError
        else:
            raise AttributeError()

    def get_config(self, name):
        r = self.dbconn.select('config', where='key=$key', vars={'key':name}).list()
        if len(r) == 0:
            raise WebUnauthorizedError
        return r[0]['value']
