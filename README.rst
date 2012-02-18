===============================================================================
percache
===============================================================================

*percache* is a Python module to persistently cache results of functions (or
callables in general) using decorators.

It is somehow similar to the `Memoize Example`_ from the Python Decorator
Library but with the advantage that results are stored *persistently* in a
cache. *percache* provides memoization across multiple invocations of the
Python interpreter.

Install by running ``easy_install percache`` or ``pip install percache``.

.. _Memoize Example: http://wiki.python.org/moin/PythonDecoratorLibrary#Memoize

-------------------------------------------------------------------------------
Example
-------------------------------------------------------------------------------

::

    >>> import percache
    >>> cache = percache.Cache("/tmp/my-cache")
    >>>
    >>> @cache
    ... def longtask(a, b):
    ...     print("running a long task")
    ...     return a + b
    ...
    >>> longtask(1, 2)
    running a long task
    3
    >>>
    >>> longtask(1, 2)
    3
    >>> cache.close() # writes new cached results to disk

As you can see at the missing output after the second invocation, ``longtask``
has been called once only. The second time the result is retrieved from the
cache.  *The key feature of this module is that this works across multiple
invocations of the Python interpreter.*

A requirement on the results to cache is that they are `pickable`_.

.. _pickable: http://docs.python.org/library/pickle.html#what-can-be-pickled-and-unpickled

Each cache file can be used for any number of differently named callables.

Alternative back-ends and live synchronization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default *percache* uses a `shelve`_ as its cache back-end. Alternative
back-ends may be used if they are given as dictionary-like objects with a
``close()`` and ``sync()`` method::

    >>> class FooCache(dict):
    ...     def sync(self):
    ...         ...
    ...     def close(self):
    ...         ...
    >>> fc = FooCache()
    >>> cache = percache.Cache(fc, livesync=True)

In this example a cache is created in live-sync mode, i.e. results
*immediately* are stored permanently. Normally this happens not until a cache's
``close()`` method has been called or until it gets `finalized`_. Note that the
live-sync mode may slow down your percache-decorated functions (though it
reduces the risk of "loosing" results).

.. _finalized: http://docs.python.org/reference/datamodel.html#object.__del__

-------------------------------------------------------------------------------
Caching details (you should know)
-------------------------------------------------------------------------------

When caching the result of a callable, a SHA1 hash based on the callable's name
and arguments is used as a key to store the result in the cache file.

The hash calculation does not work directly with the arguments but with their
*representations*, i.e. the string returned by applying ``repr()``. Argument
representations are supposed to differentiate values sufficiently for the
purpose of the function but identically across multiple invocations of the
Python interpreter. By default the built-in function ``repr()`` is used to get
argument representations. This is just perfect for basic types, lists, tuples
and combinations of them but it may fail on other types:

::

    >>> repr(42)
    42                                  # good
    >>> repr(["a", "b", (1, 2L)])
    "['a', 'b', (1, 2L)]"               # good
    >>> o = object()
    >>> repr(o)
    '<object object at 0xb769a4f8>'     # bad (address is dynamic)
    >>> repr({"a":1,"b":2,"d":4,"c":3})
    "{'a': 1, 'c': 3, 'b': 2, 'd': 4}"  # bad (order may change)
    >>> class A(object):
    ...     def __init__(self, a):
    ...         self.a = a
    ...
    >>> repr(A(36))
    '<__main__.A object at 0xb725bb6c>' # bad (A.a not considered)
    >>> repr(A(35))
    '<__main__.A object at 0xb725bb6c>' # bad (A.a not considered)

A *bad* representation is one that is not identically across Python invocations
(all *bad* examples) or one that does not differentiate values sufficiently
(last 2 *bad* examples).

To use such types anyway you can either

1. implement the type's ``__repr__()`` method accordingly or
2. provide a custom representation function using the ``repr`` keyword of the
   ``Cache`` constructor.

Implement the ``__repr__()`` method
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To pass dictionaries to *percache* decorated functions, you could wrap them in
an own dictionary type with a suitable ``__repr__()`` method:

::

    >>> class mydict(dict):
    ...     def __repr__(self):
    ...         items = ["%r: %r" % (k, self[k]) for k in sorted(self)]
    ...         return "{%s}" % ", ".join(items)
    ...
    >>> repr(mydict({"a":1,"b":2,"d":4,"c":3}))
    "{'a': 1, 'b': 2, 'c': 3, 'd': 4}"  # good (always same order)

Provide a custom ``repr()`` function
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following example shows how to use a custom representation function to get
a suitable argument representation of ``file`` objects:

::

    >>> def myrepr(arg):
    ...     if isinstance(arg, file):
    ...         # return a string with file name and modification time
    ...         return "%s:%s" % (arg.name, os.fstat(arg.fileno())[8])
    ...     else:
    ...         return repr(arg)
    ...
    >>> cache = percache.Cache("/some/path", repr=myrepr)

-------------------------------------------------------------------------------
Housekeeping
-------------------------------------------------------------------------------


- Make sure to delete the cache file whenever the behavior of a cached function
  has changed!

- To prevent the cache from getting larger and larger you can call the
  ``clear()`` method of a ``Cache`` instance. By default it clears *all*
  results from the cache. The keyword ``maxage`` my be used to specify a
  maximum number of seconds passed since a cached result has been *used* the
  last time. Any result not used (written or accessed) for ``maxage`` seconds
  gets removed from the cache.

-------------------------------------------------------------------------------
Changes
-------------------------------------------------------------------------------

Version 0.2.1
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Add missing README to PyPi package.

Version 0.2
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Automatically close (i.e. sync) the cache on finalization.
- Optionally sync the cache on each change.
- Support for alternative back-ends (others than `shelve`_).
- Cache object are callable now, which makes the explicit ``check()`` method
  obsolete (though the old interface is still supported).

.. _shelve: http://docs.python.org/library/shelve.html

Version 0.1.1
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Fix wrong usage age output of command line interface.
- Meet half way with pylint.

Version 0.1
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Initial release

