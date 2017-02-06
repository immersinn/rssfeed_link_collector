#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb  5 11:15:06 2017

@author: immersinn
"""

import utils

# RSS Entry Keymap
KEY_MAP = {'title':'title', 'link':'link', 
           'published_parsed' : 'published_parsed',
           'summary':'summary', 'id':'id'} 

# RSS Link
rss_url = "http://www.aljazeera.com/xml/rss/all.xml"
feed_list = [{'feed' : {
                       'Link' : rss_url,
                       'RssName' : 'All News',
                       'Source' : 'aljazeera'
                       }
             }]

meta = {'name' : 'Aljazeera'}
feeds_tree = utils.feeddata2xml({'meta' : meta,
                                 'feeds' : feed_list,
                                 'key_map' : KEY_MAP})
with open('data/feeds/aljazeera_feedlist.xml', 'wb') as f1:
    feeds_tree.write(f1)