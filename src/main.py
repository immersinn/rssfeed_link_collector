#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 18 21:29:36 2017

@author: immersinn
"""

import os
import logging

from utils import get_main_dir, load_feedlists
from scrape_feeds import scrapeAndSave


def main():
    # Configure logging
    fd = get_main_dir()
    logpath = os.path.join(fd, 'main_run.log')
    logging.basicConfig(filename=logpath,
                        level=logging.DEBUG,
                        format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')

    print("Retrieving contents...")
    logging.info("Retrieving contents...")
    feeds = load_feedlists()
    logging.info('Total feeedss to visit: {}'.format(len(feeds)))
    rns = scrapeAndSave(feeds, sleep_time=0.5, method='tor')
    logging.info('Total new links added from all feeds: {}'.format(len(rns)))
        
if __name__=="__main__":
    main()