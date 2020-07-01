.. peerpy documentation master file, created by
   sphinx-quickstart on Tue Jun 30 21:47:25 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Peerpy documentation
####################

This module provides a **high-level API** for discovering and connecting multiple devices on a local network, without the headache of implementing python's built-in socket module!

.. note::
   Peerpy is built on top of the python's builtin :code:`socket` module, using :code:`threading` for parallel computing, naming:
   
   * your application code
   * listening for connections
   * sending/receiving data
   * sending/answering pings

.. note::
   This module allows to quickly link the application layer (your application) to the transport layer (provided by python's :code:`socket` module) of the `OSI model <https://en.wikipedia.org/wiki/OSI_model>`_.

What is it made for?
********************

* IoT devices (e.g. Rasberry Pi)
* Blockchain
* Fast proof of concepts

Installation
************

:code:`pip install peerpy`

Source code
***********

Please refer to `python sources documentation <src.rst>`_ or `peerpy's github repository <https://github.com/Rubilmax/peerpy>`_.

.. toctree::
   :caption: Table of contents

   user_manual
   src