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
from webcommon import WebError, WebInternalError, WebBaseHandler, expose

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


class APIObjectBase:
    def __init__(self, provider=None):
        self._provider = provider or web.ctx.provider

    def dispatcher(self, method, args):
        if not args:
            func = ''
            fargs = []
        else:
            func = args[0]
            fargs = args[1:]
        try:
            fn = getattr(self, "%s_%s" % (method, func))
        except AttributeError:
            if func == '':
                return None, fargs
            if not fargs:
                func = ''
            else:
                func = fargs[0]
            try:
                fn = getattr(self, "%s_%s" % (method, func))
                fargs = (args[0],)+fargs[1:]
            except AttributeError:
                fn = None
        return fn, fargs


class RESTfulHandler(WebBaseHandler):
    def __init__(self, provider=None):
        #self.kw = {}  # just for test
        self._provider = provider or web.ctx.provider

    def dispatcher(self, method, *args):
        if not args:
            raise web.nofound()
        func = args[0]
        fargs = args[1:]
        try:
            fn = getattr(self._provider, "O_%s" % func)  # for security reason
            if isinstance(fn, APIObjectBase):
                fn, fargs = fn.dispatcher(method, fargs)
            else:
                raise AttributeError()
        except AttributeError:
            try:
                fn = getattr(self._provider, "%s_%s" % (method, func))
            except AttributeError:
                fn = None
        except:
            logger.debug(error_exc())
            fn = None
        if not fn:
            raise WebNotfoundError("Path %s not found" % "/".join(args))
        try:
            return fn(*fargs)
        except TypeError:
            raise WebNotfoundError('Path %s not found' % "/".join(args))
        except:
            raise

    @expose(format="json")
    @api_decorator
    def GET(self, *args):
        return self.dispatcher('GET', *args)

    @expose(format="json")
    @api_decorator
    def POST(self, *args):
        return self.dispatcher('POST', *args)

    @expose(format="json")
    @api_decorator
    def PUT(self, *args):
        return self.dispatcher('PUT', *args)

    @expose(format="json")
    @api_decorator
    def DELETE(self, *args):
        return self.dispatcher('DELETE', *args)


def kwargs_decorator(fn):
    def wrapper(*args, **kwargs):
        try:
            contype = web.ctx.env["CONTENT_TYPE"]
            contype.index("application/json")
            kw = json.loads(web.data())
        except:
            kw = web.input()
        arg_keys = fn.__code__.co_varnames[len(args):]
        logger.debug("kwargs_decorator, %s, %s" % (str(args), str(fn.__code__.co_varnames)))
        [kwargs.__setitem__(k,v) for k,v in kw.iteritems() if k in arg_keys]
        if 'kwargs' in arg_keys:
            kwargs['kwargs'] = kw
        logger.debug("kwargs_decorator, %s" % str(kwargs))
        return fn(*args, **kwargs)
    return wrapper

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    import unittest

    class TestWebBase(unittest.TestCase):
        def testRESTfulHandler(self):
            class Dummy:
                pass

            class Child(APIObjectBase):
                __str__ = "Child"

                def GET_(self, id=-1):
                    if id == -1:
                        return "obj1 OK"
                    else:
                        return "obj1(%s) OK" % id

                def GET_objfunc1(self):
                    return "objfunc1 OK"

                def GET_objfunc2(self, id=-1):
                    return "objfunc2(%s) called!" % id

                def GET_objfunc3(self, id=-1, *args):
                    return "obj1(%s).func3%s OK" % (id, str(args))

            class Provider:
                __str__ = "Provider"

                API_OBJECTS = {"O_obj1": Child}

                #def __init__(self):
                #    self.O_obj1 = Child(self)

                def __getattr__(self, name):
                    if self.API_OBJECTS.has_key(name):
                        return self.API_OBJECTS[name](self)
                    else:
                        raise AttributeError()

                def GET_func1(self):
                    return "func1 OK"

            provider = Provider()
            rest = RESTfulHandler(provider)
            self.assertEqual(json.loads(rest.GET('func1')), u"func1 OK")
            self.assertEqual(json.loads(rest.GET('obj1')), u"obj1 OK")
            self.assertEqual(json.loads(rest.GET('obj1', 'objfunc1')), u"objfunc1 OK")
            self.assertEqual(json.loads(rest.GET('obj1', '111')), u"obj1(111) OK")
            self.assertEqual(json.loads(rest.GET('obj1', '222', 'objfunc3')), u"obj1(222).func3() OK")
            self.assertEqual(json.loads(rest.GET('obj1', '333', 'objfunc3', '444')), u"obj1(333).func3('444',) OK")
            self.assertEqual(json.loads(rest.GET('obj1', '555', 'objfunc3', '666', 'func4')), u"obj1(555).func3('666', 'func4') OK")
            #print hasattr(rest, 'GET')

    unittest.main()
