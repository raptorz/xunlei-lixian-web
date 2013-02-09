# -*- coding: utf-8 -*-
"""
    common web class
    ~~~~~~~~~~~~~~~~
    :copyright: 2010-13 by mental.we8log.com
"""
try:
    import json
except ImportError:
    import simplejson as json
import web

from common import error_exc

import logging

logger = logging.getLogger(__name__)


class WebError(web.HTTPError):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        s = "%d %s" % (code, message)
        logger.error(s)
        web.HTTPError.__init__(self, s)


class WebBadrequestError(WebError):
    def __init__(self, message=""):
        WebError.__init__(self, 400, message or "Bad request!")


class WebUnauthorizedError(WebError):
    def __init__(self, message=""):
        WebError.__init__(self, 401, message or "Unauthorized!")


class WebForbiddenError(WebError):
    def __init__(self, message):
        WebError.__init__(self, 403, message or "Forbidden!")


class WebNotfoundError(WebError):
    def __init__(self, message=""):
        WebError.__init__(self, 404, message or "Not found!")


class WebMethodnotallowedError(WebError):
    def __init__(self, message=""):
        WebError.__init__(self, 405, message or "Method not allowed!")


class WebInternalError(WebError):
    def __init__(self, message=""):
        WebError.__init__(self, 500, message or "Internal server error! Please see log for detail!")


class WebBaseHandler:
    url_base  = '/'

    def json_render(self, page, data):
        try:
            web.header('Content-Type', 'application/json;charset=utf-8')
        except AttributeError:
            pass # just for test
        s = ""
        try:
            if data:
                s = json.dumps(data)
        except:
            logger.error(error_exc())
            raise WebInternalError("JSON encoding error! Data: %s" % str(data))
        return s

    def xml_render(self, page, data):
        web.header('Content-Type', 'text/xml;charset=utf-8')
        return getattr(self.mako_render, page)(**data)

    def render(self, page, format, data):
        try:
            render_func = getattr(self, format + '_render')
        except AttributeError:
            raise WebInternalError("Invalid render format!")
        try:
            result = render_func(page, data)
        except web.HTTPError:
            raise
        except:
            logger.error(error_exc())
            raise WebInternalError("Rendering page %s error" % (page+"."+format))
        return result

    @classmethod
    def referer_url(self):
        return web.ctx.provider.get_referer()

    @classmethod
    def home_url(self, path=""):
        return web.ctx.home + self.url_base + path

    @classmethod
    def current_url(self):
        return web.ctx.home + web.ctx.fullpath

    @classmethod
    def get_cookie(self, name, defvalue=None):
        data = web.cookies().get(name)
        if data != None:
            return json.loads(data)
        else:
            return defvalue

    @classmethod
    def set_cookie(self, name, data, expires=365, domain=None, secure=False):
        # todo: need path
        web.setcookie(name, json.dumps(data), expires*24*3600, domain, secure)

    @classmethod
    def set_error(self, error_msg):
        web.ctx.provider.set_session("last_error", error_msg)


# format : html/json/xml...
def expose(page='', format='html', debug=False):
    def expose_wrapper(fn):
        def format_wrapper(self, *args, **kwargs):
            try:
                result = fn(self, *args, **kwargs)
                # dynamic format
                if isinstance(result, dict) and 'format' in result.keys():
                    fmt = result['format']
                    del result['format']
                else:
                    fmt = format
                if fmt == 'html':
                    result['identity'] = self.get_identity()
                if not debug:
                    return self.render(page, fmt, result)
                else:
                    return result
            except WebError, e:
                logger.debug("expose WebError %s %s \n%s" % (e.code, e.message, error_exc()))
                result = ""
                if "error_handler" in dir(self):
                    result = self.error_handler(e)
                if result=="":
                    raise
                else:
                    return result
            except web.HTTPError:
                raise
            except Exception, e:
                logger.error(error_exc())
                raise WebInternalError("Expose decorator error! %s" % str(e))
        return format_wrapper
    return expose_wrapper


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    import unittest

    class TestWebBase(unittest.TestCase):
        def testWebError(self):
            def dummy():
                raise WebInternalError("Test error")

            self.assertRaises(WebError, dummy())

    unittest.main()
