#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb  5 10:51:01 2017

@author: immersinn
"""

import utils
import requests
from bs4 import BeautifulSoup as bs


# URL Resources
fox_url = "http://www.foxnews.com/about/rss/"
base_feed_url = "http://feeds.foxnews.com/foxnews"


# RSS Entry Keymap
KEY_MAP = {'title':'title', 'link':'link', 
           'published_parsed' : 'published_parsed',
           'summary':'summary', 'id':'link'}


# Fetch Page
response = requests.get(fox_url)
if response.ok:
    page = response.content
else:
    page = bytes()


# Parse respnse, get feeds
soup = bs(page, 'html.parser') 
feed_list = soup.find('div', {'class':'section-mod list'})
feed_list = feed_list.findAll('li')[1:]
feed_list = [{'feed' : {
                        'Link' : li.a['data-url'],
                        'RssName' : li.a['data-type'],
                        'Name' : li.text.strip(),
                        'Source' : 'foxnews',
                       }
             }
            for li in feed_list]


# Store Feeds as XML
meta = {'name' : 'FoxNews'}
fxt = utils.feeddata2xml({'meta' : meta,
                          'feeds' : feed_list,
                          'key_map' : KEY_MAP})
with open('data/feeds/foxnews_feedlist.xml', 'wb') as f1:
    fxt.write(f1)