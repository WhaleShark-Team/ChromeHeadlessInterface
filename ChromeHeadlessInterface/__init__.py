#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
    ChromeHeadlessInterface
    ~~~~~~~~~~~~~~~~~~~~~~~

    Chrome headless protocol interface.

    :author:    lightless <root@lightless.me>
    :homepage:  None
    :file:      __init__.py
"""

from __future__ import unicode_literals
from __future__ import print_function

import json
import threading

import requests
import websocket

from api import ChromeAPI


class ChromeHeadlessInterface(object):

    def __init__(self, host="localhost", port="9222", timeout=5, debug=False):
        super(ChromeHeadlessInterface, self).__init__()

        self._host = host
        self._port = port
        self._lock = threading.Lock()
        self._tab = None
        self._event_table = []
        self._command_id = 1
        self._timeout = timeout
        self._user_command_id = None
        self._debug = debug

        if not self._open_new_tab():
            raise RuntimeError("Can not open new tab.")

    def __del__(self):
        self.close()

    def _close_tab(self):
        url = ChromeAPI.CLOSE_TAB_URL.format(self._host, self._port, self._tab.get("tab_id"))
        try:
            requests.get(url)
            return True
        except Exception as e:
            print("Error while closing tab.")
            print("Details error: {0}".format(e))
            return False

    def _open_new_tab(self):
        url = ChromeAPI.OPEN_NEW_TAB_URL.format(self._host, self._port)
        try:
            response = requests.get(url)
        except Exception as e:
            print("Error while access {0}, please check chrome browser.".format(url))
            print("Details error: {0}".format(e))
            return False
        response = response.json()
        tab_id = response.get("id")
        if not tab_id:
            return False
        ws_url = response.get("webSocketDebuggerUrl")
        if not ws_url:
            return False

        ws_instance = websocket.create_connection(ws_url, timeout=self._timeout)
        if not ws_instance:
            return False

        self._tab = {
            "tab_id": tab_id,
            "ws_url": ws_url,
            "ws_instance": ws_instance
        }
        return self._tab

    def _call_event_listener(self, event_name, params):
        # 在这里遍历用户监听的事件表
        for e in self._event_table:
            if e.get("event_name") == event_name:
                if self._debug:
                    print("[DEBUG] hit event: {0}".format(event_name))
                # 命中了用户监听的事件，依次调用 callback
                for cb in e.get("callback"):
                    cb(params)

    def open_new_tab(self):
        return self._open_new_tab()

    def add_event_listener(self, event, callback):

        added = False

        for e in self._event_table:

            if added:
                return True

            if e.get("event_name", "") == event:
                e["callback"].append(callback)
                added = True

        if not added:
            self._event_table.append({
                "event_name": event,
                "callback": [callback]
            })
            return True

    def send_command(self, command, params=None, command_id=None):
        if not params:
            params = {}
        if not command:
            print("Error command: {0}".format(command))
            return False
        if command_id and isinstance(command_id, int):
            self._user_command_id = command_id

        payload = {
            "id": command_id if command_id else self._command_id,
            "method": command,
            "params": params
        }
        ws_instance = self._tab.get("ws_instance")
        ws_instance.send(json.dumps(payload))

        if command_id:
            return command_id
        else:
            self._command_id += 1
            return self._command_id - 1

    def recv_until_string(self, expected_string):

        ws_result = []
        ws_instance = self._tab.get("ws_instance")

        while True:
            try:
                result = ws_instance.recv()
            except websocket.WebSocketTimeoutException:
                return ws_result

            if self._debug:
                print("[DEBUG] result: {0}".format(result))
            if not result:
                return ws_result

            # 提取结果
            ws_result.append(result)

            # 调用用户定义的事件
            formatted_result = json.loads(result)
            event_name = formatted_result.get("method")
            params = formatted_result.get("params")
            self._call_event_listener(event_name, params)

            # 查找结束标志
            if expected_string in result:
                break
        return ws_result

    def recv_by_special_id(self, command_id=None):

        if command_id:
            expected_id = command_id
        else:
            expected_id = self._command_id

        ws_result = []
        ws_instance = self._tab.get("ws_instance")

        while True:
            try:
                result = ws_instance.recv()
            except websocket.WebSocketTimeoutException:
                return ws_result

            if self._debug:
                print("[DEBUG] result: {0}".format(result))
            if not result:
                return ws_result

            # 提取结果
            ws_result.append(result)

            # 调用用户定义的事件
            formatted_result = json.loads(result)
            event_name = formatted_result.get("method")
            params = formatted_result.get("params")
            self._call_event_listener(event_name, params)

            # 查找结束标志
            if int(formatted_result.get("id", 0)) == expected_id-1:
                break
        return ws_result

    def recv(self, expected_string="", command_id=None):

        if expected_string:
            return self.recv_until_string(expected_string)
        else:
            return self.recv_by_special_id(command_id)

    def close(self):
        self._close_tab()
        if self._tab.get("ws_instance"):
            self._tab.get("ws_instance").close()


