#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 18 21:10:56 2017

@author: immersinn
"""

from time import mktime
from datetime import date, datetime
import feedparser

TO_KEEP = ['title', 'link', 'published_parsed', 'summary', 'id', 'rss_link']
KEY_LOOKUP = {'title':'title', 'link':'link', 
              'published_parsed':'published',
              'summary':'summary', 'id':'story_id', 'rss_link':'rss_link'}

              
def get_feed_contents(rss_entry):
    feed = feedparser.parse(rss_entry['Link'])
    if feed.entries:
        contents = feed.entries
        for c in contents:
            c['rss_link'] = rss_entry['Link']
    else:
        contents = []
    contents = [{KEY_LOOKUP[key] : c[key] for key in TO_KEEP} for c in contents]
    for c in contents:
        c['published'] = datetime.fromtimestamp(mktime(c['published']))
    return(contents)
    

def scrape_feeds(rss_feeds):
    contents = []
    for rss_entry in rss_feeds:
        contents.extend(get_feed_contents(rss_entry))
    return(contents)
