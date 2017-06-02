#!/bin/env python
# -*- encoding:utf-8 -*-
"""
    ChromeHeadLess
    ~~~~~~~~~~

    ChromeHeadLess驱动
    :author = 'wilson;lightless'
"""

import json
import requests
import websocket


class ChromeHeadLess(object):
    def __init__(self, url, ip="127.0.0.1", port="9222", cookie="", post="", auth=""):
        """
        初始化
        :param url: 请求url
        :param ip: ChromeHeadless的server ip
        :param port: ChromeHeadless的server 端口
        :param cookie: 请求cookie
        :param post:  请求post Chrome的api不支持
        :param auth:  请求 authorization
        """
        self.url = url
        self.cookie = cookie
        self.post = post
        self.auth = auth
        self.ip = ip
        self.port = port
        self.tab_id = ""
        self.ws_url = ""
        self.hook_urls = []
        self.error = ""
        self.soc = None
        self.javascript_dialog_events = []
        chrome_web = "http://%s:%s/json/new" % (ip, port)
        try:
            response = requests.get(chrome_web)
            self.ws_url = response.json().get("webSocketDebuggerUrl")
            self.tab_id = response.json().get("id")
            self.soc = websocket.create_connection(self.ws_url)
            # print(self.ws_url, self.tab_id)
        except Exception, e:
            # print "ERROR:%s" % e
            self.error = str(e)

    def close_tab(self):
        """
        关闭tab
        :return:
        """
        try:
            requests.get("http://%s:%s/json/close/%s" % (self.ip, self.port, self.tab_id))
        except Exception, e:
            #print "ERROR:%s" % e
            self.error = str(e)

    def send_msg(self, id, method, params):
        """
        给ChromeHeadless的server 发执行命令
        :param id:
        :param method:
        :param params:
        :return:
        """
        # soc = websocket.create_connection(ws_url)
        navcom = json.dumps({
            "id": id,
            "method": method,
            "params": params
        })
        self.soc.send(navcom)

    def get_chrome_msg(self):
        """
        循环监听
        :return:
        """
        while True:
            result = self.soc.recv()
            result_json = json.loads(result)
            # print("debug:%s" % result)
            if "Network.requestWillBeSent" in result:
                # hook url
                if result_json["params"]["request"]["url"] not in self.hook_urls:
                    if "postData" in result_json["params"]["request"]:
                        post = result_json["params"]["request"]["postData"]
                    else:
                        post = ""
                    self.hook_urls.append({
                        "url": result_json["params"]["request"]["url"],
                        "method": result_json["params"]["request"]["method"],
                        "post": post
                    })

            if "Page.javascriptDialogOpening" in result:
                # hook alert
                if result_json["params"] not in self.javascript_dialog_events:
                    self.javascript_dialog_events.append(result_json["params"])

            if "Page.domContentEventFired" in result:
                # dom加载完以后 执行on事件的javascript
                (self.send_msg(id=2333, method="Runtime.evaluate", params={"expression": "\nvar nodes = document.all;"
                                                                                         "\nfor(var i=0;i<nodes.length;i++){"
                                                                                         "\n    var attrs = nodes[i].attributes;"
                                                                                         "\n    for(var j=0;j<attrs.length;j++){"
                                                                                         "\n        attr_name = attrs[j].nodeName;"
                                                                                         "\n        attr_value = attrs[j].nodeValue.replace(/return.*;/g,'');"
                                                                                         "\n        if(attr_name.substr(0,2) == \"on\"){"
                                                                                         "\n            console.log(attrs[j].nodeName + ' : ' + attr_value);"
                                                                                         "\n            eval(attr_value);"
                                                                                         "\n        }"
                                                                                         "\n        if(attr_name == \"href\" || attr_name == \"formaction\"){"
                                                                                         "\n            console.log(attrs[j].nodeName + ' : ' + attr_value);"
                                                                                         "\n            javascript_code = attr_value.match(\"^javascript:(.*)\")"
                                                                                         "\n           if (javascript_code) {"
                                                                                         "\n               eval(javascript_code[0]);"
                                                                                         "\n           }"
                                                                                         "\n        }"
                                                                                         "\n    }"
                                                                                         "\n}"
                                                                                         "\n'ok';"}))

            if "id" in result_json:
                if result_json["id"] == 2333:
                    # onevent 事件 执行结束
                    # 关闭 tab 页面
                    self.close_tab()
                    return

    def run(self):
        if self.soc:
            (self.send_msg(id=1, method="Network.setExtraHTTPHeaders", params={"headers": {
                "authorization": self.auth,
                "Cookie": self.cookie,
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 Safari/537.36"}}))

            self.send_msg(id=2, method="Network.enable", params={})

            self.send_msg(id=3, method="Page.enable", params={})

            self.send_msg(id=4, method="Runtime.enable", params={})

            self.send_msg(id=5, method="Page.navigate", params={"url": self.url})

            # if self.post != "":
            #     (self.send_msg(id=5, method="Runtime.evaluate",
            #                    params={"expression": "httpRequest = new XMLHttpRequest();"
            #                                          "\nhttpRequest.open(\"POST\",\"%s\",true);"
            #                                          "\nhttpRequest.setRequestHeader(\"Content-type\",\"application/x-www-form-urlencoded\")"
            #                                          "\nhttpRequest.onreadystatechange = function (){"
            #                                          "\nif (httpRequest.readyState == 4 && httpRequest.status == 200) {"
            #                                          "\n        alert(httpRequest.responseText);"
            #                                          "\n  }"
            #                                          "\n}"
            #                                          "\nhttpRequest.send(\"%s\");"
            #                                          "\n'ok';"
            #                                          "" % (self.url, self.post)}))
            # else:
            #     self.send_msg(id=5, method="Page.navigate", params={"url": self.url})

            self.get_chrome_msg()
        else:
            self.error = "get websocket err!"


if __name__ == '__main__':
    chrome_headless_drive = ChromeHeadLess(url="http://127.0.0.1/url.php?url=1342",
                                           ip="127.0.0.1", port="9222",
                                           cookie="",
                                           post="",
                                           auth="")
    chrome_headless_drive.run()
    print chrome_headless_drive.hook_urls
    print chrome_headless_drive.javascript_dialog_events

