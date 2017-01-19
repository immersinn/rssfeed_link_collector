#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 18 21:29:36 2017

@author: immersinn
"""

import os
import logging

from utils import get_main_dir, load_feedlists
from scrape_feeds import scrape_feeds
from mysql_utils import saveNewLinks


def main():
    fd = get_main_dir()
    logpath = os.path.join(fd, 'main_run.log')
    logging.basicConfig(filename=logpath,level=logging.DEBUG)

    logging.debug("Retrieving contents...")
    feeds = load_feedlists()
    contents = scrape_feeds(feeds)
    if contents:
        logging.debug('Total entries retrieved: {}'.format(len(contents)))
        rns = saveNewLinks(contents)
        logging.debug('Total new links added: {}'.format(len(rns)))
    else:
        logging.debug('No contents found')
        
        
if __name__=="__main__":
    main()