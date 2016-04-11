.. _api:

Python API
==========

The pytoutv Python API is pretty straightforward:

#. Create a :py:class:`toutv3.client.Client` with appropriate
   TOU.TV credentials.
#. Get shows, sections, or summaries, from this client instance.
#. Read the :py:attr:`toutv3.Model.Show.media_versions` or
   :py:attr:`toutv3.Model.EpisodeLineupItem.media_versions` property
   to get a list of available media versions.
#. At this point, you can create a :py:class:`toutv3.download.Download`
   object by calling
   :py:meth:`toutv3.Model.MediaVersion.create_download`.
#. When you're done, call :py:meth:`toutv3.client.Client.release_cache`
   to release the cache lock taken when creating the client (see
   :ref:`cache` for more information).

.. note::

   The current API requires a client to be logged in: it does not
   allow anonymous connections to TOU.TV.

.. toctree::

   examples
   reference


.. _cache:

Cache
-----

Almost all the network operations (except when downloading media
content) of pytoutv have their results registered into a per-TOU.TV user
cache file. This accelerates further network requests which would
result in the same responses.

When this cache is created or loaded (at client creation time),
it's protected by a cache lock file which must be explicitly released.
Once the cache lock is released, further network operations are not
cached.

The cache expiration time is set to 30 minutes.

The cache directory lookup order is:

#. ``$TOUTV3_CACHE_DIR`` (environment variable). This is the full
   path to a directory (existing or not).
#. On Linux platforms:

   a. ``$XDG_CACHE_HOME/toutv3``, if ``$XDG_CACHE_HOME`` is set
   b. ``$HOME/.cache/toutv3``

#. ``$PWD/.toutv3-cache``

If, for any reason, a cache file cannot be created, no exception is
raised: no cache is used by the created client.


.. _logging:

Logging
-------

Logging statements are placed at strategic locations in the source code
to help with debugging the Python package, should anything change on
the TOU.TV API side, for example.

All :py:mod:`toutv3` loggers are children of the ``toutv3`` logger. You
may also enable the logging statements of the underlying
`Requests <http://docs.python-requests.org/>`_ package by setting the
desired level of the ``requests`` logger.
