#!/usr/bin/env python

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

"""Utility to persistently cache results of callables using decorators.

See http://pypi.python.org/pypi/percache for usage instructions and examples.

"""

import hashlib
from os.path import exists
import shelve
import sys
import time

# =============================================================================

class Cache(object):
    """Persistent cache for results of callables."""

    def __init__(self, backend, repr=repr, livesync=False):
        """Create a new persistent cache using the given backend.

	If backend is a string, it is interpreted as a filename and a Python
	shelve is used as the backend. Otherwise it is interpreted as a
	mapping-like object with a `close()` and a `sync()`  method. This
	allows to use alternative backends like *shove* or *redis*.

	The keyword `repr` may specify an alternative representation function
	to be applied to the arguments of callables to cache. The
	representation function is used when calculating a hash of the
	arguments. Representation functions need to differentiate argument
	values sufficiently (for the purpose of the callable) and identically
	across different invocations of the Python interpreter. The default
	representation function `repr()` is suitable for basic types, lists,
	tuples and combinations of them as well as for all types which
	implement the `__repr__()` method according to the requirements
	mentioned above.

        Normally changes are only written to the cache when it is closed or
	finalized. If `livesync` is `True`, the cache is written to the backend
	whenever it changes.

        """
        self.__livesync = livesync
        self.__repr = repr
        if isinstance(backend, basestring):
            self.__cache = shelve.open(backend, protocol=-1)
        else:
            self.__cache = backend
        self.check = self.__call__ # support old decorator interface

    def __call__(self, func):
        """Decorator function for caching results of a callable."""

        def wrapper(*args, **kwargs):
            """Function wrapping the decorated function."""

            ckey = hashlib.sha1(func.__name__) # parameter hash
            for a in args:
                ckey.update(self.__repr(a))
            for k in sorted(kwargs):
                ckey.update("%s:%s" % (k, self.__repr(kwargs[k])))
            ckey = ckey.hexdigest()

            if ckey in self.__cache:
                result = self.__cache[ckey]
            else:
                result = func(*args, **kwargs)
                self.__cache[ckey] = result
            self.__cache["%s:atime" % ckey] = time.time() # access time
            if self.__livesync:
                self.__cache.sync()
            return result

        return wrapper

    def __del__(self):
        """Closes the cache upon finalization."""

        self.close()

    def close(self):
        """Close cache and save it to the backend."""

        self.__cache.close()

    def clear(self, maxage=0):
        """Clear all cached results or those not used for `maxage` seconds."""

        if maxage > 0:
            outdated = []
            bigbang = time.time() - maxage
            for key in self.__cache:
                if key.endswith(":atime") and self.__cache[key] < bigbang:
                    outdated.append(key)
                    outdated.append(key.rsplit(":", 1)[0])

            for key in outdated:
                del self.__cache[key]
        else:
            self.__cache.clear()

    def stats(self):
        """Get some statistics about this cache.

        Returns a 3-tuple containing the number of cached results as well as
        the oldest and most recent result usage times (in seconds since epoch).

        """
        num = 0
        oldest = time.time()
        newest = 0
        for key in self.__cache:
            if key.endswith(":atime"):
                num += 1
                oldest = min(oldest, self.__cache[key])
                newest = max(newest, self.__cache[key])
        return num, oldest, newest

# =============================================================================
# Command line functionality
# =============================================================================

def _main():
    """Command line functionality."""

    def age(s):
        """Pretty-print an age given in seconds."""

        m, h, d = s // 60, s // 3600, s // 86400
        for val, unit in ((d, "d"), (h, "h"), (m, "m"), (s, "s")):
            if val > 1 or unit == "s":
                return "%d%s" % (val, unit)

    if len(sys.argv) != 2:
        print("Usage: %s CACHEFILE" % sys.argv[0])
        sys.exit(1)

    if not exists(sys.argv[1]):
        print("no such cache file")
        sys.exit(1)

    c = Cache(sys.argv[1])
    now = time.time()
    num, oldest, newest = c.stats()
    print("Number of cached results : %d" % num)
    print("Oldest result usage age  : %s" % age(now - oldest))
    print("Latest result usage age  : %s" % age(now - newest))

if __name__ == '__main__':
    _main()
