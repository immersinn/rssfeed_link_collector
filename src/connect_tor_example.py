# see here for installing tor:
# https://www.torproject.org/docs/debian

# http://icanhazip.com/


import socks
import socket
from sockshandler import SocksiPyHandler

""""
DO NOT USE THIS METHOD

Note that monkeypatching may not work for all standard modules or for all 
third party modules, and generally isn't recommended. Monkeypatching is 
usually an anti-pattern in Python.

DO NOT USE THIS METHOD
"""
socks.setdefaultproxy(proxy_type=socks.PROXY_TYPE_SOCKS5, 
                      addr="127.0.0.1", 
                      port=9050)
socket.socket = socks.socksocket

import requests
print(requests.get("http://icanhazip.com").text)


"""Use this method"""
import urllib
opener = urllib.request.build_opener(SocksiPyHandler(socks.SOCKS5,
                                                     "127.0.0.1",
                                                     9050))
# All requests made by the opener will pass through the SOCKS proxy
print(opener.open("http://icanhazip.com"))

