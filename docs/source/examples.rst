.. _examples:

API usage examples
==================

All the examples below use ``sys.argv[1]`` and ``sys.argv[2]`` for resp.
getting the user name and the password. Run them like this:

.. code-block:: none

   python example.py my@email.address my.password

.. note::

   The examples below do not catch :ref:`exceptions <exceptions>`,
   but any serious application using pytoutv should handle them
   properly.


List searchable shows
---------------------

.. code-block:: python

   import toutv3.client
   import sys


   # create client
   client = toutv3.client.Client(sys.argv[1], sys.argv[2])

   # get the list of searchable shows
   shows = client.search_show_summaries

   # list them
   for show in shows:
       print('{}:'.format(show.title))
       print('  URL name:        {}'.format(show.url))
       print('  Searchable text: {}'.format(show.searchable_text))
       print('  Is free?:        {}'.format(show.is_free))

   # always release the cache when you're done!
   client.release_cache()


List section summaries
----------------------

.. code-block:: python

   import toutv3.client
   import sys


   # create client
   client = toutv3.client.Client(sys.argv[1], sys.argv[2])

   # get the list of section summaries
   section_summaries = client.section_summaries

   # list them
   for section_summary_name, section_summary in section_summaries.items():
       print('{}:'.format(section_summary.title))
       print('  Name: {}'.format(section_summary_name))

   # release the cache
   client.release_cache()


List the subsections and shows of a specific section
----------------------------------------------------

The specific section's name is read from ``sys.argv[3]`` here. Run the
example like this:

.. code-block:: none

   python example.py my@email.address my.password section-name

.. code-block:: python

   import toutv3.client
   import sys


   # create client
   client = toutv3.client.Client(sys.argv[1], sys.argv[2])

   # get the specific section
   section = client.get_section(sys.argv[3])

   # print section's title
   print('Title: {}'.format(section.title))

   # list subsection lineups
   for subsection in section.subsection_lineups:
       print()
       print('Subsection: {}'.format(subsection.title))

       # list show items in subsection lineup
       for show_item in subsection.items:
           print('  {}'.format(show_item.title))
           print('    URL name: {}'.format(show_item.url))
           print('    Is free?: {}'.format(show_item.is_free))

   # release the cache
   client.release_cache()


List the seasons and episodes of a specific show
------------------------------------------------

The specific show's URL name is read from ``sys.argv[3]`` here. Run the
example like this:

.. code-block:: none

   python example.py my@email.address my.password show-url-name

The URL name of a show can be found in the
:py:attr:`toutv3.model.SearchShowSummary.url` or
:py:attr:`toutv3.model.ShowLineupItem.url` property.

.. code-block:: python

  import toutv3.client
  import sys


  # create client
  client = toutv3.client.Client(sys.argv[1], sys.argv[2])

  # get the specific show
  show = client.get_show(sys.argv[3])

  # print show's title
  print('Title: {}'.format(show.title))

  # list season lineups
  for season in show.season_lineups:
      print()
      print('Season: {}'.format(season.title))

      # list episode items in season lineup
      for episode_item in season.items:
          print('  {}'.format(episode_item.title))
          print('    URL name: {}'.format(episode_item.url))
          print('    Is free?: {}'.format(episode_item.is_free))

  # release the cache
  client.release_cache()


Download latest episode of latest season of specific show
---------------------------------------------------------

The specific show's URL name is read from ``sys.argv[3]`` here. Run the
example like this:

.. code-block:: none

   python example.py my@email.address my.password show-url-name

The URL name of a show can be found in the
:py:attr:`toutv3.model.SearchShowSummary.url` or
:py:attr:`toutv3.model.ShowLineupItem.url` property.

.. code-block:: python

   import toutv3.client
   import sys


   # create client
   client = toutv3.client.Client(sys.argv[1], sys.argv[2])

   # get the specific show
   show = client.get_show(sys.argv[3])

   # get the latest episode of the latest season
   season = show.season_lineups[-1]
   episode = season.items[-1]

   # print show, season, and episode titles
   print('Show:    {}'.format(show.title))
   print('Season:  {}'.format(season.title))
   print('Episode: {}'.format(episode.title))
   print()

   # get the list of media versions of this show
   media_versions = episode.media_versions

   # pick the media version with the lowest quality
   media_version = media_versions[0]

   # create a download object
   download = media_version.create_download()

   # download media version to "/tmp/episode.ts"
   last_printed_dl_segments = None

   for progress in download.iter_download('/tmp/episode.ts'):
       if progress.dl_segments != last_printed_dl_segments:
           print('{}/{}'.format(progress.dl_segments,
                                progress.total_segments))
           last_printed_dl_segments = progress.dl_segments

   # release the cache
   client.release_cache()
