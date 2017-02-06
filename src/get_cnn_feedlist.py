#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 01:49:43 2017

@author: immersinn
"""

import utils
import requests
from bs4 import BeautifulSoup as bs


# URL Resources
rss_url = "http://www.cnn.com/services/rss/"


# RSS Entry Keymap
KEY_MAP = {'title':'title', 'link':'feedburner_origlink', 
           'published_parsed' : 'published_parsed',
           'summary':'summary', 'id':'id'}


# Fetch Page, Make Soup
response = requests.get(rss_url)
if response.ok:
    page = response.content
else:
    page = bytes()
soup = bs(page, 'html.parser')


# Extract Container, Feeds
container = soup.find('td', {'class' : 'cnnBodyText'})
contents = container.findAll('tr', {'valign' : 'top'})[2:]
feed_list = []
for tr in contents:
    tds = tr.findAll('td', {'class' : 'cnnBodyText'})
    feed_list.append({'feed' :{
                               'RssName' : tds[0].text.strip(),
                               'Link' : tds[1].a['href'],
                               'Source' : 'cnn'
                               }
                     })
    
    
# Store Feeds as XML
meta = {'name' : 'CNN'}
feeds_tree = utils.feeddata2xml({'meta' : meta,
                                 'feeds' : feed_list,
                                 'key_map' : KEY_MAP})
with open('data/feeds/cnnmain_feedlist.xml', 'wb') as f1:
    feeds_tree.write(f1)