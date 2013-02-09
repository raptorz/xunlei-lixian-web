#coding=utf-8
'''
    common class
    ~~~~~~~~~~~~~~~~

    :copyright: 2010-13 by mental.we8log.com
'''

def error_exc():
    import traceback
    return traceback.format_exc()


class DataRow(dict):
    def __init__(self, inobj={}, objfields=[], attribute=None):
        self.attribute = attribute
        indict = {}
        if isinstance(inobj, dict):
            indict = inobj
            inobj = None
        dict.__init__(self, self.fields_filter(indict, objfields))
        self.__initialised = True
        if not inobj is None:
            self.from_object(inobj, objfields)

    def __getattr__(self, item):
        try:
            return self.__getitem__(item)
        except KeyError:
            raise AttributeError(item)

    def __setattr__(self, item, value):
        if not '_DataRow__initialised' in self.__dict__.keys():  # this test allows attributes to be set in the __init__ method
            return dict.__setattr__(self, item, value)
        elif item in self.__dict__.keys():       # any normal attributes are handled normally
            dict.__setattr__(self, item, value)
        else:
            self.__setitem__(item, value)

    def from_object(self, inobj, objfields=[]):
        [self.__setitem__(k, getattr(inobj, k)) for k in (objfields != []) and objfields or [n for n in dir(inobj) if n[:1] != '_' and n != 'metadata']]

    def fields_filter(self, indict, objfields=[]):
        r = {}
        [r.__setitem__(k, v) for k,v in indict.iteritems() if objfields==[] or k in objfields]
        return r


if __name__ == "__main__":
    import unittest

    class TestUtils(unittest.TestCase):
        def testError_exc(self):
            try:
                raise ValueError("Test")
            except:
                print error_exc()

        def testDataRow(self):
            foo = dict(k11="v11", k12="v12")
            df = DataRow(foo)
            self.assertEqual(df.k11, "v11")

            class dummy:
                pass

            bar = dummy()
            bar.k21 = "v21"
            bar.k22 = "v22"
            db = DataRow(inobj=bar, objfields=['k21'])
            self.assertEqual(db["k21"], "v21")
            self.assertRaises(KeyError, lambda : db["k22"])

            df.from_object(bar, objfields=['k22'])
            self.assertEqual(df.k12, "v12")
            self.assertEqual(df["k22"], "v22")
            self.assertRaises(AttributeError, lambda : df.k21)


    unittest.main()
