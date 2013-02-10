# -*- coding: utf-8 -*-
"""
    web api base for web.py
    ~~~~~~~~~~~~~~~~
    :copyright: 2010-13 by mental.we8log.com
"""
try:
    import json
except ImportError:
    import simplejson as json
import web

from common import error_exc, DataRow
from webcommon import WebNotfoundError, WebBaseHandler, expose

import logging

logger = logging.getLogger(__name__)


def api_decorator(fn):
    def wrapper(self, *args, **kwargs):
        result = fn(self, *args, **kwargs)
        if result!=None and (not isinstance(result, DataRow)) and (not isinstance(result, str)) and (not isinstance(result, unicode)):
            if isinstance(result, list):
                if len(result)>0 and not isinstance(result[0], DataRow):
                    result = [DataRow(inobj=u) for u in result]
            else:
                result = DataRow(inobj=result)
        return result
    return wrapper


# must static decorator in web.py
class RestBaseHandler(WebBaseHandler):
    def __dispatch(self, method, *args):
        if not args:
            func = ''
            fargs = []
        else:
            func = args[0]
            fargs = args[1:]
        try:
            fn = getattr(self, "%s_%s" % (method, func))
        except AttributeError:
            if not fargs:
                func = ''
            else:
                func = fargs[0]
            try:
                fn = getattr(self, "%s_%s" % (method, func))
                fargs = (args[0],)+fargs[1:]
            except AttributeError:
                fn = None
        if fn:
            return fn(*fargs)
        else:
            raise WebNotfoundError("Path %s not found" % "/".join(args))

    @expose(format="json")
    @api_decorator
    def GET(self, *args):
        return self.__dispatch('GET', *args)

    @expose(format="json")
    @api_decorator
    def POST(self, *args):
        return self.__dispatch('POST', *args)

    @expose(format="json")
    @api_decorator
    def PUT(self, *args):
        return self.__dispatch('PUT', *args)

    @expose(format="json")
    @api_decorator
    def DELETE(self, *args):
        return self.__dispatch('DELETE', *args)


def kwargs_decorator(fn):
    def wrapper(*args, **kwargs):
        try:
            contype = web.ctx.env["CONTENT_TYPE"]
            contype.index("application/json")
            kw = json.loads(web.data())
        except:
            kw = web.input()
        arg_keys = fn.__code__.co_varnames[len(args):]
        [kwargs.__setitem__(k,v) for k,v in kw.iteritems() if k in arg_keys]
        if 'kwargs' in arg_keys:
            kwargs['kwargs'] = kw
        return fn(*args, **kwargs)
    return wrapper

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    import unittest


    class TestAPIServer(unittest.TestCase):
        def testRestBaseHandler(self):
            class APIHandler(RestBaseHandler):
                __str__ = "Child"

                def GET(self, id=""):
                    return "ID is %s" % id

            rest = APIHandler()
            self.assertEqual(json.loads(rest.GET('1')), u"ID is 1")


    unittest.main()
