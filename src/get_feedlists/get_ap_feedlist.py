#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 02:41:51 2017

@author: immersinn
"""

import utils
import requests
from bs4 import BeautifulSoup as bs


# URL Resources
rss_url = "http://hosted.ap.org/dynamic/fronts/RSS_FEEDS?SITE=AP"


# RSS Entry Keymap
KEY_MAP = {'title':'title', 'link':'link', 
           'published_parsed' : 'published_parsed',
           'summary':'summary', 'id':'link'}


# Fetch Page, Make Soup
response = requests.get(rss_url)
if response.ok:
    page = response.content
else:
    page = bytes()
soup = bs(page, 'html.parser')


# Extract feeds
container = soup.find('td', {'width' : "466"})
tables = container.findAll('table')[1:]
feed_list = [{'feed' :{
                       'Link' : table.find('td', {'height' : '13'}).a['href'],
                       'RssName' : table.find('td', {'height' : '13'}).text.strip(),
                       'Source' : 'associatedpress'
                       }
             }
            for table in tables]
    
    
# Store Feeds as XML
meta = {'name' : 'AssociatedPress'}
feeds_tree = utils.feeddata2xml({'meta' : meta,
                                 'feeds' : feed_list,
                                 'key_map' : KEY_MAP})
with open('data/feeds/ap_feedlist.xml', 'wb') as f1:
    feeds_tree.write(f1)