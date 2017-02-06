#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb  5 11:19:37 2017

@author: immersinn
"""

import utils
import requests
from bs4 import BeautifulSoup as bs


# URL Resources
new_text_rss_base = "http://feeds.bbci.co.uk/news/"
old_text_rss_base = "http://newsrss.bbc.co.uk/rss/newsonline_uk_edition/"
new_aav_rss_base = "http://feeds.bbci.co.uk/news/video_and_audio/"
old_aav_rss_base = "http://newsrss.bbc.co.uk/rss/newsplayer_uk_edition/"
feed_url_01 = "http://news.bbc.co.uk/2/hi/help/rss/default.stm"
feed_url_02 = "http://www.bbc.com/news/10628494"


# RSS Entry Keymap
KEY_MAP = {'title':'title', 'link':'link', 
           'published_parsed' : 'published_parsed',
           'summary':'summary', 'id':'id'}


# Process the 1st page
page = requests.get(url=feed_url_01).content
soup = bs(page, 'html.parser')
feed_containers = [soup.findAll('ul', {'class' : 'rss'})[0]]

feed_list = []
for container in feed_containers:
    feed_list.extend([{'feed' : {
                                 'Link' : li.a['href']\
                                             .replace(old_text_rss_base, new_text_rss_base)\
                                             .replace(old_aav_rss_base, new_aav_rss_base),
                                 'RssName' : li.text.strip(),
                                 'Source' : 'bbc'
                                 }
                      }
                      for li in container.findAll('li')])
    
    
# Process the 2nd Page
page = requests.get(url=feed_url_02).content
soup = bs(page, 'html.parser')
feed_containers = soup.findAll('div', {'class' : "pullout-inner"})
feed_containers = [fc for fc in feed_containers \
                   if fc.text.strip().split('\n')[0].endswith('Feeds')]

for container in feed_containers:
    feed_list.extend([{'feed' : {
                                 'Link' : p.a['href']\
                                             .replace(old_text_rss_base, new_text_rss_base)\
                                             .replace(old_aav_rss_base, new_aav_rss_base),
                                 'RssName' : p.text.strip(),
                                 'Source' : 'bbc'
                                 }
                      }
                      for p in container.findAll('p')[1:]])
    
    
# Cleanup (i.e. remove dupes)
clean_feed_list = []
feed_urls = set()
for feed in feed_list:
    if feed['feed']['Link'] not in feed_urls:
        feed_urls.update(set([feed['feed']['Link']]))
        clean_feed_list.append(feed)
feed_list = clean_feed_list
del(clean_feed_list)

# dead reckon clean:
replace_list = {"http://feeds.bbci.co.uk/news/sci/tech/rss.xml" : "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
                "http://newsrss.bbc.co.uk/rss/newsonline_uk_edition/uk_politics/rss.xml" : "http://feeds.bbci.co.uk/news/politics/rss.xml",
                }
for feed in feed_list:
    if feed['feed']['Link'] in replace_list.keys():
        feed['feed']['Link'] = replace_list[feed['feed']['Link']]
        

# *cough cough*
remove_list = ['http://feeds.bbci.co.uk/news/uk_politics/rss.xml',
'http://feeds.bbci.co.uk/news/entertainment/rss.xml',
'http://feeds.bbci.co.uk/news/talking_point/rss.xml',
'http://feeds.bbci.co.uk/news/system/latest_published_content/rss.xml']
feed_list = [feed for feed in feed_list if feed['feed']['Link'] not in remove_list]
    

# Store Feeds as XML
meta = {'name' : 'BBCNews'}
feeds_tree = utils.feeddata2xml({'meta' : meta,
                                 'feeds' : feed_list,
                                 'key_map' : KEY_MAP})
with open('data/feeds/bbcnews_feedlist.xml', 'wb') as f1:
    feeds_tree.write(f1)