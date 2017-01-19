#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 18 20:04:57 2017

@author: immersinn
"""

import os
import pickle
import xml.etree.ElementTree as ET


def get_main_dir():
    fd = os.path.split(os.path.realpath(os.path.split(__file__)[0]))[0]
    return(fd)
    

def get_feedlists_dir():
    fd = get_main_dir()
    feeds_dir = os.path.join(fd, "data/feeds/")
    return(feeds_dir)


def get_feedlists_files():
    feeds_dir = get_feedlists_dir()
    feeds_files = os.listdir(feeds_dir)
    return(feeds_files)
    
    
def load_feedlist(feeds_file):
    feeds_file = os.path.join(get_feedlists_dir(), feeds_file)
    with open(feeds_file, 'rb') as f1:
        feeds = pickle.load(f1)
    return(feeds)

    
def load_feedlists():
    feeds_files = get_feedlists_files()
    feeds = []
    for feeds_file in feeds_files:
        feeds.extend(load_feedlist(feeds_file))
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
    
    
if __name__ == "__main__":
    files = get_feedlists_files()
    print(files)
    feeds = load_feedlists()
    print('Total feeds: {}'.format(len(feeds)))
    print(feeds[0])
    print(feeds[-1])