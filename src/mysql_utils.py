#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 18 21:51:50 2017

@author: immersinn
"""

import utils

import mysql.connector
from mysql.connector.cursor import MySQLCursor
from mysql.connector.errors import IntegrityError


DB = "articles"
TABLE = "rssfeed_links"


def saveNewLinks(links):
    """
    
    """
    u,p = utils.get_creds('MySQL')
    cnx = mysql.connector.connect(user=u, password=p, database=DB)
    cur = MySQLCursor(cnx)
    
    try:
        exists = lambda l: exists_base(cur, l)
        links = [l for l in links if not exists(l)]
        row_nbrs = dump_entries(cur, links)
        cnx.commit()
        
    except IntegrityError:
        cnx.rollback()
        
    finally:
        cur.close()
        cnx.close()
        
    return(row_nbrs)


def dump_entries(cursor, entries):
    
    add_entry = ("INSERT INTO " + TABLE + " "
                 "(title, link, published, summary, story_id, rss_link) "
                 "VALUES (%(title)s, %(link)s, %(published)s, %(summary)s, %(story_id)s, %(rss_link)s)")
    
    rows = []
    dls = set()
    for entry in entries:
        if entry['link'] not in dls:
            cursor.execute(add_entry, entry)
            rows.append(cursor.lastrowid)
            dls.update([entry['link']])
        
    return(rows)


def exists_base(cursor, entry):
    sqlq = "SELECT (1) FROM " + TABLE + " WHERE link = '{}' LIMIT 1"
    cursor.execute(sqlq.format(entry['link']))
    if cursor.fetchone():
        return(True)
    else:
        return(False)

        
if __name__=="__main__":
    
    fd = utils.get_main_dir()
    test_contents_dir = utils.os.path.join(fd,
                                           "data/interim/test_feedlinks.pkl")
    with open(test_contents_dir, 'rb') as f1:
        contents = utils.pickle.load(f1)
        
    print(len(contents))
    
    rns = saveNewLinks(contents)
                
    print(rns[:10])