GRAPHIES
===========

``graphies`` is a Python library for representing graphs as token sequences.
Inspired by `SELFIES`_, GRAPHIES strings can be decoded to always produce graphs that obey maximum degree constraints.
In molecular graphs, this enables generation of always valid bond topologies for any GRAPHIES string.


.. toctree::
   :maxdepth: 2

   grammar
   decoder
   encoder
   api

.. _SELFIES: https://github.com/aspuru-guzik-group/selfies