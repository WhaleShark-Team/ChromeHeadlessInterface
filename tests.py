#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
    package path
    ~~~~~~~~~~~~

    package description

    :author:    lightless <root@lightless.me>
    :homepage:  None
    :file:      tests.py
"""

from ChromeHeadlessInterface import ChromeHeadlessInterface


def hook(params):
    print("detected alert!")


chi = ChromeHeadlessInterface()

chi.add_event_listener("Page.javascriptDialogOpening", hook)
# chi.add_event_listener("Page.javascriptDialogOpening", hook2)

chi.send_command("Page.enable")
result = chi.recv()
print(result)

chi.send_command("Page.navigate", {"url": "http://x.x.x.x/a.html"})
result = chi.recv("Page.domContentEventFired")
print(result)

chi.close()

