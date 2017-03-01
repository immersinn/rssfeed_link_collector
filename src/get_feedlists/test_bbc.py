#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 04:19:59 2017

@author: immersinn
"""

import time
import itertools
import utils
import scrape_feeds
from urllib.error import HTTPError



if __name__=="__main__":
    feeds = utils.load_feedlist_data('bbcnews_feedlist.xml')
    openers = [utils.configure_tor_opener() for _ in range(8)]
    openers = itertools.cycle(openers)
    
    for ent_id, opener in zip(range(len(feeds)), openers):
        rss_entry = feeds[ent_id]
        try:
            contents = scrape_feeds.get_feed_contents(rss_entry, 
                                                      method='tor',
                                                      opener=opener)
        except HTTPError:
            print(rss_entry['Link'])
            
        time.sleep(0.2)