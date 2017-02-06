#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb  5 23:12:03 2017

@author: immersinn
"""

import utils


# RSS Entry Keymap
KEY_MAP = {'title':'title', 'link':'link', 
           'published_parsed' : 'published_parsed',
           'summary':'summary', 'id':'id'}


rss_url = "http://feeds.feedburner.com/breitbart?format=xml"
feed_list = [{'feed' : {
                        'Link' : rss_url,
                        'RssName' : 'All News',
                        'Source' : 'breitbart'
                        }
             }]


# Store Feeds as XML
meta = {'name' : 'Breitbart'}
feeds_tree = utils.feeddata2xml({'meta' : meta,
                                 'feeds' : feed_list,
                                 'key_map' : KEY_MAP})
with open('data/feeds/breitbart_feedlist.xml', 'wb') as f1:
    feeds_tree.write(f1)
