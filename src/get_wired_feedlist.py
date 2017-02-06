#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 01:31:53 2017

@author: immersinn
"""

import utils
import requests
from bs4 import BeautifulSoup as bs


# URL Resources
rss_url = "https://www.wired.com/about/rss_feeds"


# RSS Entry Keymap
KEY_MAP = {'title':'title', 'link':'link', 
           'published_parsed' : 'published_parsed',
           'summary':'summary', 'id':'id'}


# Fetch Page, Make Soup
response = requests.get(rss_url)
if response.ok:
    page = response.content
else:
    page = bytes()
soup = bs(page, 'html.parser')


# Extract feeds
container = soup.find('article', {'class' : 'content link-underline relative body-copy'})
feed_list = [{'feed' : {
                        'Link' : p.a['href'],
                        'RssName' : p.a.text.strip(),
                        'Source' : 'wired'
                       }
             }
             for p in container.findAll('p')]


# Store Feeds as XML
meta = {'name' : 'Wired'}
feeds_tree = utils.feeddata2xml({'meta' : meta,
                                 'feeds' : feed_list,
                                 'key_map' : KEY_MAP})
with open('data/feeds/wired_feedlist.xml', 'wb') as f1:
    feeds_tree.write(f1)