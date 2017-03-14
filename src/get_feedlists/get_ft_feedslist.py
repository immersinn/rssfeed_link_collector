#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb  5 23:17:56 2017

@author: immersinn
"""

import utils
import requests
from bs4 import BeautifulSoup as bs


# URL Resources
rss_url = "http://www.ft.com/rss?ft_site=falcon&desktop=true"

BAD_FEEDS = ["http://www.ft.com/rss/management/connected-business",
             "http://www.ft.com/rss/world/mideast/economy",
             ]


# RSS Entry Keymap
KEY_MAP = {'title':'title', 'link':'link', 
           'published_parsed' : 'published_parsed',
           'summary':'summary', 'id':'ft_uid'}


# Fetch Page, Make Soup
response = requests.get(rss_url)
if response.ok:
    page = response.content
else:
    page = bytes()
soup = bs(page, 'html.parser')


# Extract target list sections
link_lists = soup.findAll('div', {'class' : 'linkList'})
keep_sections = ['Homepages', 
                 'Companies by Sector', 'Companies by Region',
                 'World', 'Markets', 'Technology',]
link_lists = [ll for ll in link_lists if ll.a.text.strip() in keep_sections]


# Extract all feed links from target list sections
feed_list = []
for ll in link_lists:
    feed_list.extend([{'feed' : {
                                 'Link' : li.a['href'],
                                 'RssName' : li.text.strip(),
                                 'Source' : 'FinancialTimes'
                                 }
                      }
                     for li in ll.findAll('li')])
feed_list = [fl for fl in feed_list if fl['feed']['Link'] not in BAD_FEEDS]
    
    
# Store Feeds as XML
meta = {'name' : 'FT'}
feeds_tree = utils.feeddata2xml({'meta' : meta,
                                 'feeds' : feed_list,
                                 'key_map' : KEY_MAP})
with open('data/feeds/ft_feedlist.xml', 'wb') as f1:
    feeds_tree.write(f1)
