#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 02:22:56 2017

@author: immersinn
"""

import utils
#import requests
#from bs4 import BeautifulSoup as bs


# URL Resources
rss_url = "https://www.theguardian.com/help/feeds"
base_url = "https://www.theguardian.com/"


# RSS Entry Keymap
KEY_MAP = {'title':'title', 'link':'link', 
           'published_parsed' : 'published_parsed',
           'summary':'summary', 'id':'id'}


# Bit of a "hand curated" list; see "rss_url"
feeds = [{'Link' : "https://www.theguardian.com/science",
          'RssName' : 'science'},
         {'Link' : "https://www.theguardian.com/us/technology",
          'RssName' : 'tech-us'},
         {'Link' : "https://www.theguardian.com/uk/technology",
          'RssName' : 'tech-uk'},
         {'Link' : "https://www.theguardian.com/us/business",
          'RssName' : 'business-us'},
         {'Link' : "https://www.theguardian.com/uk/business",
          'RssName' : 'business-uk'},
          {'Link' : "https://www.theguardian.com/us/environment",
          'RssName' : 'environment-us'},
         {'Link' : "https://www.theguardian.com/uk/environment",
          'RssName' : 'environment-uk'}]
feed_list = []
for feed in feeds:
    feed['Link'] = feed['Link'] + '/rss'
    feed['Source'] = 'theguardian'
    feed_list.append({'feed' : feed})


# Store Feeds as XML
meta = {'name' : 'Guardian'}
feeds_tree = utils.feeddata2xml({'meta' : meta,
                                 'feeds' : feed_list,
                                 'key_map' : KEY_MAP})
with open('data/feeds/guardian_feedlist.xml', 'wb') as f1:
    feeds_tree.write(f1)