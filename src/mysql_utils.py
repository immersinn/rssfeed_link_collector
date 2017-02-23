#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 18 21:51:50 2017

@author: immersinn
"""

import time
import logging

import pandas
import mysql.connector
from mysql.connector.cursor import MySQLCursor
from mysql.connector.errors import IntegrityError

import utils


DB = "articles"
TABLES = ['rssfeed_links', 'words', 'doc_bows']
TABLE = TABLES[0]


def getCnx():
    u,p = utils.get_creds('MySQL')
    cnx = mysql.connector.connect(user=u, password=p, database=DB)
    return(cnx)


def getCur(cnx):
    return(MySQLCursor(cnx))


def dfDocsFromCursor(cursor):
    return(pandas.DataFrame(data = cursor.fetchall(),
                            columns = cursor.column_names))


def saveNewLinks(links):
    """
    
    """
    u,p = utils.get_creds('MySQL')
    cnx = mysql.connector.connect(user=u, password=p, database=DB)
    cur = MySQLCursor(cnx)
    
    try:
        exists = lambda l: exists_base(cur, l)
        links = [l for l in links if not exists(l)]
#        logging.info('Total new links found: {}'.format(len(links)))
        row_nbrs = dump_entries(cur, links)
        cnx.commit()
        
    except IntegrityError:
        cnx.rollback()
        
    except BaseException as err:
        err_type = str(type(err))
        err_msg = str(err.args)
        logging.error("Error encountered: " + err_type + ': ' + err_msg)
		
        
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
    
    
def query_docs_by_datetime(cursor, 
                           start_dt, end_dt='Now',
                           fields = ['link', 'title', 'rss_link', 'summary', 'published']):
    
    date_query_base = '''SELECT ''' + \
                      ', '.join(fields) + \
                      ''' FROM rssfeed_links WHERE published BETWEEN %s AND %s'''
    
    if end_dt=='Now':
        end_dt = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
        
    cursor.execute(date_query_base, (start_dt, end_dt))
    return(dfDocsFromCursor(cursor))


def query_docs_details(cursor, doc_ids, 
                       fields=['link', 'title', 'summary', 'published']):
    
    format_strings = ','.join(['%s'] * len(doc_ids))
    doc_query_base = '''SELECT ''' + \
                  ', '.join(fields) + \
                  ''' FROM rssfeed_links WHERE link IN (%s)''' % format_strings
    
    cursor.execute(doc_query_base, (doc_ids))
    return(dfDocsFromCursor(cursor))
        
    

        
if __name__=="__main__":
    
    fd = utils.get_main_dir()
    test_contents_dir = utils.os.path.join(fd,
                                           "data/interim/test_feedlinks.pkl")
    with open(test_contents_dir, 'rb') as f1:
        contents = utils.pickle.load(f1)
        
    print(len(contents))
    
    rns = saveNewLinks(contents)
                
    print(rns[:10])
