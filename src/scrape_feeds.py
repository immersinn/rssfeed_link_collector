#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 18 21:10:56 2017

@author: immersinn
"""

import os
import itertools
from time import mktime, sleep, gmtime
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
        
    keymap = rss_entry.pop('keymap')
    keymap['rss_link'] = 'rss_link'
    
    new_contents = []
    for c in contents:
        nd = {}
        for key in TO_KEEP:
            try:
                nd[KEY_LOOKUP[key]] = c[keymap[key]]
            except KeyError:
                if key == 'published_parsed':
                    nd[KEY_LOOKUP[key]] = gmtime()
                elif key == 'id':
                    nd[KEY_LOOKUP[key]] = c[keymap['link']]
        new_contents.append(nd)
                    
#    contents = [{KEY_LOOKUP[key] : c[keymap[key]] for key in TO_KEEP} for c in contents]
    
    contents = new_contents
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


def scrapeAndSave(feeds, sleep_time=.2, n_openers=4, method='tor', verbose=False):
    
    if method=='tor':
        logging.info("Creating {} Tor openers...".format(n_openers))
        openers = [configure_tor_opener() for _ in range(n_openers)]
        ip_addr = openers[0].open("http://icanhazip.com").read().strip()
        logging.info("IP Used: " + str(ip_addr))
        if verbose:
            print(ip_addr)
    else: 
        openers = [None]
    openers = itertools.cycle(openers)
    
    rns = []
    for ent_id, opener in zip(range(len(feeds)), openers):
        rss_entry = feeds[ent_id]
        
        try:
            contents = get_feed_contents(rss_entry, method=method, opener=opener)
            
            if contents:
                logging.info('Total entries retrieved from {}: {}'.format(rss_entry['Link'],
                                                                          len(contents)))
                new_rns = saveNewLinks(contents)
                logging.info('Total new links added: {}'.format(len(new_rns)))
                rns.extend(new_rns)
            else:
                logging.info('No contents found')
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except BaseException as err:
            err_type = str(type(err))
            err_msg = str(err.args)
            logging.error("Feed " + str(rss_entry['Link']) + ": " + err_type + ': ' + err_msg)
        
        sleep(sleep_time)
        
    return(rns)