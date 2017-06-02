#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
    ChromeHeadlessInterface.api
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    API URL in Chrome.

    :author:    lightless <root@lightless.me>
    :homepage:  None
    :file:      api.py
"""

from __future__ import unicode_literals


class ChromeAPI(object):
    TAB_LIST_URL = "http://{0}:{1}/json"
    OPEN_NEW_TAB_URL = "http://{0}:{1}/json/new"
    CLOSE_TAB_URL = "http://{0}:{1}/json/close/{2}"
