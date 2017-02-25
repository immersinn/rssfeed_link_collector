#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 03:24:54 2017

@author: immersinn
"""

import utils
from urllib.request import urlopen
#import requests
from bs4 import BeautifulSoup as bs


# URL Resources
rss_url = "https://phys.org/feeds/"


# RSS Entry Keymap
KEY_MAP = {'title':'title', 'link':'link', 
           'published_parsed' : 'published_parsed',
           'summary':'summary', 'id':'id'}


# Fetch Page, Make Soup
#response = requests.get(rss_url)
#if response.ok:
#    page = response.content
#else:
#    page = bytes()
page = urlopen(rss_url).read()
soup = bs(page, 'html.parser')


# Extract feeds
feeds = soup.find_all('tr')
feed_list = []

for f in feeds[1:]:
    name = []
    all_stories = ''
    bre_stories = ''
    
    try:
        name = f.strong.text
        category = name
    except AttributeError:
        pass
    
    if not name:
        tds = f.find_all('td')
        name = tds[1].text
        
    hrefs = f.find_all('a')
    if hrefs:
        all_stories = hrefs[0]['href']
        if len(hrefs) > 1:
            bre_stories = hrefs[1]['href']  
        
    feed_list.append({'feed' : {
                                'RssName' : name,
                                'Category' : category,
                                'AllStories' : all_stories,
                                'Spotlight' : bre_stories,
                                'Link' : all_stories,
                                'Source' : 'physorg'
                                }
                     })
    
    
# Store Feeds as XML
meta = {'name' : 'PhysOrg'}
feeds_tree = utils.feeddata2xml({'meta' : meta,
                                 'feeds' : feed_list,
                                 'key_map' : KEY_MAP})
with open('data/feeds/physorg_feedlist.xml', 'wb') as f1:
    feeds_tree.write(f1)