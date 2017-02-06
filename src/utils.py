#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 18 20:04:57 2017

@author: immersinn
"""

import os
import xml.etree.ElementTree as ET
import socks
from sockshandler import SocksiPyHandler
from urllib import request


    
def configure_tor_opener():
    
    opener = request.build_opener(SocksiPyHandler(socks.SOCKS5,
                                                  "127.0.0.1",
                                                  9050))
    return(opener)


def get_main_dir():
    fd = os.path.split(os.path.realpath(os.path.split(__file__)[0]))[0]
    return(fd)
    

def get_feedlists_dir():
    fd = get_main_dir()
    feeds_dir = os.path.join(fd, "src/data/feeds/")
    return(feeds_dir)


def get_feedlists_files():
    feeds_dir = get_feedlists_dir()
    feeds_files = [ff for ff in os.listdir(feeds_dir) if ff.endswith(".xml")]
    return(feeds_files)


def load_feedlist_data(feeds_file):
    feeds_file = os.path.join(get_feedlists_dir(), feeds_file)
    feeds = feedsFromXML(feeds_file)
    keymap = keymapFromXML(feeds_file)
    for feed in feeds:
        feed['keymap'] = keymap
    return(feeds)

    
def load_feedlists_data():
    feeds_files = get_feedlists_files()
    feeds = []
    for feeds_file in feeds_files:
        feeds.extend(load_feedlist_data(feeds_file))
    return(feeds)
    
    
def get_creds(name):
    fd = get_main_dir()
    cred_path = os.path.join(fd, 'credentials.creds')
    tree = ET.parse(cred_path)
    root = tree.getroot()
    
    keep = ET.Element('')
    username = ''
    password = ''
    
    for elem in root:
        if elem.attrib['name'] == name:
            keep = elem
    if keep.tag:
        username = keep.find('username').text
        password = keep.find('password').text
        
    return(username, password)


def feedsFromXML(feeds_file):
    # load the file
    tree = ET.ElementTree()
    tree.parse(feeds_file)
    feeds_list = []
    feeds = [f for f in tree.find('feeds')]
    for feed in feeds:
        feeds_list.append({c.tag : c.text for c in feed.getchildren()})
    return(feeds_list)


def keymapFromXML(feeds_file):
    tree = ET.ElementTree()
    tree.parse(feeds_file)
    key_map = {c.tag : c.text for c in tree.find('key_map').getchildren()}
    return(key_map)
    

#def xmlFromDict(meta, feeds):
#    
#    root = ET.Element('data')
#    mele = ET.SubElement(root, 'meta')
#    for k,v in meta.items():
#        m = ET.SubElement(mele, k)
#        m.text = v
#    fele = ET.SubElement(root, 'feeds')
#    for feed in feeds:
#        f = ET.SubElement(fele, 'feed')
#        for k,v in feed.items():
#            e = ET.SubElement(f, k)
#            e.text = v
#    tree = ET.ElementTree(root)
#    return(tree)


def dict2xml(d, root=ET.Element('data')):
    for key,val in d.items():
        if type(val) == str:
            e = ET.SubElement(root, key)
            e.text = val
        elif type(val) == list:
            ele = ET.SubElement(root, key)
            list2subele(val, ele)
        elif type(val) == dict:
            ele = ET.SubElement(root, key)
            _ = dict2xml(val, ele)
            
    return(root)


def list2subele(li, parent_ele):
    for item in li:
        if type(item) == dict:
            _ = dict2xml(item, root=parent_ele)
        else:
            for k,v in item.items():
                e = ET.SubElement(parent_ele, k)
                e.text = v


def feeddata2xml(feed_data):
    xml_ele = dict2xml(feed_data)
    xml_tree = ET.ElementTree(xml_ele)
    return(xml_tree)
    
    
if __name__ == "__main__":
    files = get_feedlists_files()
    print(files)
    feeds = load_feedlists_data()
    print('Total feeds: {}'.format(len(feeds)))
    print(feeds[0])
    print(feeds[-1])