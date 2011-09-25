# -*- coding: utf-8 -*-

# =============================================================================
#
#    percache - persistently cache results of callables using decorators.
#
#    Copyright (C) 2010 by Oben Sonne <obensonne@googlemail.com>
#
#    This file is part of percache.
#
#    Permission is hereby granted, free of charge, to any person
#    obtaining a copy of this software and associated documentation
#    files (the "Software"), to deal in the Software without
#    restriction, including without limitation the rights to use,
#    copy, modify, merge, publish, distribute, sublicense, and/or sell
#    copies of the Software, and to permit persons to whom the
#    Software is furnished to do so, subject to the following
#    conditions:
#
#    The above copyright notice and this permission notice shall be
#    included in all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#    OTHER DEALINGS IN THE SOFTWARE.
#
# =============================================================================

import os
import os.path
import tempfile
import time

import unittest

from percache import Cache

TESTFILE = os.path.join(tempfile.gettempdir(), "percache.tests")

class TestCase(unittest.TestCase):

    def __init__(self, *args):

        if os.path.exists(TESTFILE):
            os.remove(TESTFILE)
        super(TestCase, self).__init__(*args)

    def setUp(self):
        unittest.TestCase.setUp(self)

    def tearDown(self):
        unittest.TestCase.tearDown(self)

    def call(self, fn, name, args, kwargs, result, cached):
        expstr = "expecting %s result" % (cached and "cached" or "new")
        print("calling %s(%s | %s) (%s)" % (name, args, kwargs, expstr))
        self.frun = False
        r = fn(*args, **kwargs)
        self.assertTrue(cached ^ self.frun)
        self.assertTrue(result == r)

    def test_1(self):
        """Test differentiation of basic numeric arguments."""

        c = Cache(TESTFILE)

        @c
        def f1(a, b):
            print("computing new result")
            self.frun = True
            return a

        @c
        def f2(a, b):
            print("computing new result")
            self.frun = True
            return a

        self.call(f1, "f1", (1,2), {}, 1, False)
        self.call(f1, "f1", (1,2), {}, 1, True)
        self.call(f1, "f1", (1,2L), {}, 1, False)
        self.call(f1, "f1", (1,3), {}, 1, False)
        self.call(f2, "f2", (1,3), {}, 1, False)
        self.call(f2, "f2", (1,3), {}, 1, True)
        self.call(f2, "f2", (1.1,0.1), {}, 1.1, False)
        self.call(f2, "f2", (1.1,0.1), {}, 1.1, True)

        c.close()

    def test_2(self):
        """Test persistency of cached results."""

        c = Cache(TESTFILE)

        @c
        def f1(a, b):
            print("computing new result")
            self.frun = True
            return a

        @c
        def f2(a, b):
            print("computing new result")
            self.frun = True
            return a

        c = Cache(TESTFILE)

        self.call(f1, "f1", (1,2), {}, 1, True)
        self.call(f1, "f1", (1,2L), {}, 1, True)
        self.call(f1, "f1", (1,3), {}, 1, True)
        self.call(f2, "f2", (1,3), {}, 1, True)
        self.call(f2, "f2", ("2",3), {}, "2", False)
        self.call(f2, "f2", ("2",3), {}, "2", True)

        c.close()

    def test_3(self):
        """Test differentiation of normal and unicode strings."""

        c = Cache(TESTFILE)

        @c
        def f3(s):
            print("computing new result")
            self.frun = True
            return None

        self.call(f3, "f3", ("a",), {}, None, False)
        self.call(f3, "f3", (u"a",), {}, None, False)
        self.call(f3, "f3", ("a",), {}, None, True)
        self.call(f3, "f3", (u"a",), {}, None, True)

        c.close()

    def test_4(self):
        """Free"""

    def test_5(self):
        """Test clearing of old cached results."""

        c = Cache(TESTFILE)

        @c
        def f5(a):
            print("computing new result")
            self.frun = True
            return a

        self.call(f5, "f5", (1,), {}, 1, False)
        time.sleep(2)
        self.call(f5, "f5", (2,), {}, 2, False)

        c.clear(maxage=1)

        self.call(f5, "f5", (1,), {}, 1, False)
        self.call(f5, "f5", (2,), {}, 2, True)

        c.close()

    def test_6(self):
        """Test keyword arguments."""

        c = Cache(TESTFILE)

        @c
        def f6(a, x=1, y=2, z=3):
            print("computing new result")
            self.frun = True
            return a + x + y + z

        self.call(f6, "f6", (1,), {"z":1,"y":1}, 4, False)
        self.call(f6, "f6", (1,), {"z":1,"y":1}, 4, True)
        self.call(f6, "f6", (1,), {"y":1,"z":1}, 4, True)
        self.call(f6, "f6", (1,), {"y":0,"z":2}, 4, False)
        self.call(f6, "f6", (1,), {"z":2,"y":0}, 4, True)

        c.close()

    def test_7(self):
        """Test overridden __repr__ method."""

        c = Cache(TESTFILE)

        class X(object):
            def __init__(self, a):
                self.a = a
            def __repr__(self): return repr(self.a)

        class Y(object):
            def __init__(self, a):
                self.a = a

        @c
        def f7(a):
            print("computing new result")
            self.frun = True
            return 0

        self.call(f7, "f7", (X(1),), {}, 0, False)
        self.call(f7, "f7", (X(1),), {}, 0, True)
        self.call(f7, "f7", (X(2),), {}, 0, False)

        y1, y2 = Y(1), Y(1)

        self.call(f7, "f7", (y1,), {}, 0, False)
        self.call(f7, "f7", (y2,), {}, 0, False) # bad __repr__ method

        c.close()

    def test_8(self):
        """Test custom repr function."""

        def myrepr(a):
            return "foobar"

        c = Cache(TESTFILE, repr=myrepr)

        class X(object): pass

        @c
        def f8(a):
            print("computing new result")
            self.frun = True
            return 0

        x1, x2, x3 = X(), X(), X()
        self.call(f8, "f8", (x1,), {}, 0, False)
        self.call(f8, "f8", (x2,), {}, 0, True)
        self.call(f8, "f8", (x3,), {}, 0, True) # stupid repr function
        self.call(f8, "f8", (5,), {}, 0, True) # stupid repr function

        c.close()

    def test_check(self):
        """Test if old `check` interface still works."""

        c = Cache(TESTFILE)

        @c.check
        def f1(a, b):
            print("computing new result")
            self.frun = True
            return a

        @c.check
        def f2(a, b):
            print("computing new result")
            self.frun = True
            return a

        self.call(f1, "f1", (1,2), {}, 1, False)
        self.call(f1, "f1", (1,2), {}, 1, True)
        self.call(f1, "f1", (1,2L), {}, 1, False)
        self.call(f1, "f1", (1,3), {}, 1, False)
        self.call(f2, "f2", (1,3), {}, 1, False)
        self.call(f2, "f2", (1,3), {}, 1, True)
        self.call(f2, "f2", (1.1,0.1), {}, 1.1, False)
        self.call(f2, "f2", (1.1,0.1), {}, 1.1, True)

        c.close()

    def test_alternative_backend(self):
        """Test alternative backend and live-sync mode."""

        class Backend(dict):
            """Dummy backend."""
            closed = False
            synced = False
            def close(self):
                self.closed = True
            def sync(self):
                self.synced = True

        b = Backend()
        c = Cache(b, livesync=True)

        @c
        def f1(a, b):
            print("computing new result")
            self.frun = True
            return a

        @c
        def f2(a, b):
            print("computing new result")
            self.frun = True
            return a

        self.call(f1, "f1", (1,2), {}, 1, False)
        self.call(f1, "f1", (1,2), {}, 1, True)
        self.call(f1, "f1", (1,2L), {}, 1, False)
        self.call(f1, "f1", (1,3), {}, 1, False)
        self.call(f2, "f2", (1,3), {}, 1, False)
        self.call(f2, "f2", (1,3), {}, 1, True)
        self.call(f2, "f2", (1.1,0.1), {}, 1.1, False)
        self.call(f2, "f2", (1.1,0.1), {}, 1.1, True)

        self.assertTrue(b.synced)
        self.assertFalse(b.closed)
        c.close()
        self.assertTrue(b.closed)

        # now without live-sync

        b = Backend()
        c = Cache(b, livesync=False)

        @c
        def f3(a, b):
            print("computing new result")
            self.frun = True
            return a

        @c
        def f4(a, b):
            print("computing new result")
            self.frun = True
            return a

        self.call(f3, "f1", (1,2), {}, 1, False)
        self.call(f3, "f1", (1,2), {}, 1, True)
        self.call(f3, "f1", (1,2L), {}, 1, False)
        self.call(f3, "f1", (1,3), {}, 1, False)
        self.call(f4, "f2", (1,3), {}, 1, False)
        self.call(f4, "f2", (1,3), {}, 1, True)
        self.call(f4, "f2", (1.1,0.1), {}, 1.1, False)
        self.call(f4, "f2", (1.1,0.1), {}, 1.1, True)

        self.assertFalse(b.synced)
        c.close()

if __name__ == '__main__':

    unittest.main()

