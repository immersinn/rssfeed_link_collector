# see here for installing tor:
# https://www.torproject.org/docs/debian

# http://icanhazip.com/


import socks
import socket

socks.setdefaultproxy(proxy_type=socks.PROXY_TYPE_SOCKS5, 
                      addr="127.0.0.1", 
                      port=9050)
socket.socket = socks.socksocket

import requests
print(requests.get("http://icanhazip.com").text)

