#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 18 21:10:56 2017

@author: immersinn
"""

from time import mktime, sleep
from datetime import date, datetime
import logging

import requests
import feedparser

from utils import configure_tor_opener
from mysql_utils import saveNewLinks


TO_KEEP = ['title', 'link', 'published_parsed', 'summary', 'id', 'rss_link']
KEY_LOOKUP = {'title':'title', 'link':'link', 
              'published_parsed':'published',
              'summary':'summary', 'id':'story_id', 'rss_link':'rss_link'}

              
              
def process_feed_contents(feed, rss_entry):
    """
    """
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
              
              
def get_feed_contents(rss_entry, method='basic', opener=None):
    if method=='basic':
        return(get_feed_contents_basic(rss_entry))
    elif method=="tor":
        return(get_feed_contents_tor(rss_entry, opener))
        
        
def get_feed_contents_basic(rss_entry):
    feed = feedparser.parse(rss_entry['Link'])
    return(process_feed_contents(feed, rss_entry))
    
    
def get_feed_contents_tor(rss_entry, opener):
    page = opener.open(rss_entry['Link']).read()
    feed = feedparser.parse(page)
    return(process_feed_contents(feed, rss_entry))
    

def scrape_feeds(rss_feeds, sleep_time = 1):
    contents = []
    for rss_entry in rss_feeds:
        contents.extend(get_feed_contents(rss_entry))
        sleep(sleep_time)
    return(contents)

    
def scrapeAndSave(rss_feeds, sleep_time=1, method='basic'):
    
    if method=='tor':
        opener = configure_tor_opener()
        ip_addr = opener.open("http://icanhazip.com").read().strip()
        logging.info("IP Used: " + str(ip_addr))
        print(ip_addr)
    else: 
        opener = None
    
    rns = []
    for rss_entry in rss_feeds:
        contents = get_feed_contents(rss_entry, method=method, opener=opener)
    
        if contents:
            logging.info('Total entries retrieved from {}: {}'.format(rss_entry['Link'],
                                                                      len(contents)))
            new_rns = saveNewLinks(contents)
            logging.info('Total new links added: {}'.format(len(new_rns)))
            rns.extend(new_rns)
        else:
            logging.info('No contents found')
        
        sleep(sleep_time)
        
    return(rns)