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
from mysql.connector.errors import IntegrityError, ProgrammingError

import utils


DB = "articles"
TABLES = ['rssfeed_links', 'words', 'doc_bows']
TABLE = TABLES[0]


########################################
## General Helper functions
########################################


def getCnx():
    u,p = utils.get_creds('MySQL')
    cnx = mysql.connector.connect(user=u, password=p, database=DB)
    return(cnx)


def getCur(cnx):
    return(MySQLCursor(cnx))


def dfDocsFromCursor(cursor):
    return(pandas.DataFrame(data = cursor.fetchall(),
                            columns = cursor.column_names))
    

def dictDocFromCursor(cursor):
    return({k : f for f, k in zip(cursor.next(),
                                  cursor.column_names)})


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
    
    
########################################
## Pre-hashed query functions
########################################
    
    
def query_docsByDatetime(cursor, 
                           start_dt, end_dt='Now',
                           fields = ['link', 'title', 'rss_link', 'summary', 'published']):
    
    date_query_base = '''SELECT ''' + \
                      ', '.join(fields) + \
                      ''' FROM rssfeed_links WHERE published BETWEEN %s AND %s'''
    
    if end_dt=='Now':
        end_dt = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
        
    cursor.execute(date_query_base, (start_dt, end_dt))
    return(dfDocsFromCursor(cursor))


def query_docsDetails(cursor, doc_ids, 
                       fields=['link', 'title', 'summary', 'published']):
    
    format_strings = ','.join(['%s'] * len(doc_ids))
    doc_query_base = '''SELECT ''' + \
                  ', '.join(fields) + \
                  ''' FROM rssfeed_links WHERE link IN (%s)''' % format_strings
    
    cursor.execute(doc_query_base, (doc_ids))
    return(dfDocsFromCursor(cursor))


def query_backgroundWordInfo(cur, word_ids):
    wids_format = ", ".join([str(wid) for wid in word_ids])
    query = "SELECT * FROM words_info WHERE word_id IN ({})".format(wids_format)
    cur.execute(query)
    result = dfDocsFromCursor(cur)
    return(result)


def query_totalEntries(cur, table):
    if table == "rssfeed_links":
        key = "link"
    query = "SELECT COUNT(DISTINCT {}) FROM {}".format(key, table)
    cur.execute(query)
    return(cur.fetchall()[0][0])


def query_wordIDLookup(cur, words):
    format_strings = ','.join(["%s"] * len(words))
    query = ("SELECT id, word FROM words "
             "WHERE word IN ({})".format(format_strings))
    cur.execute(query, list(words))
    cols = cur.column_names
    word_lookup = [{cols[0] : e[0], cols[1] : e[1]} for e in cur.fetchall()]
    word_lookup = {e['id'] : e['word'] for e in word_lookup}
    return(word_lookup)


def query_idWordLookup(cur, wids):
    format_strings = ','.join(["%s"] * len(wids))
    query = ("SELECT id, word FROM words "
             "WHERE id IN ({})".format(format_strings))
    cur.execute(query, list(wids))
    cols = cur.column_names
    word_lookup = [{cols[0] : e[0], cols[1] : e[1]} for e in cur.fetchall()]
    word_lookup = {e['id'] : e['word'] for e in word_lookup}
    return(word_lookup)


def query_docsOnWords(cur, words, word_type="id", exclude_docs=set()):
    
    if word_type == "word":
        word_doc_query = ("SELECT doc_bows.doc_id, doc_bows.wcount "
                          "FROM  doc_bows LEFT JOIN words ON (doc_bows.word_id = words.id) "
                          "WHERE words.word = '{}' ")
    elif word_type == "id":
        word_doc_query = ("SELECT doc_bows.doc_id, doc_bows.wcount "
                          "FROM  doc_bows LEFT JOIN words ON (doc_bows.word_id = words.id) "
                          "WHERE words.id = '{}' ")

    doc_ids = set()
    word_count_store = []
    for word in words:
        cur.execute(word_doc_query.format(word))
        result = dfDocsFromCursor(cur)
        result = result[[i not in exclude_docs for i in result['doc_id']]]
        if result.shape[0] > 0:
            doc_ids.update(set(result['doc_id']))
            word_count_store.append({'word' : word,
                                     'n_docs' : result.shape[0],
                                     'n_tot' : result['wcount'].sum()})

    doc_ids = [int(i) for i in doc_ids]
    word_count_store = pandas.DataFrame(word_count_store)
        
    return(doc_ids, word_count_store)


def query_wordSummaryInfo(cur, words, wtype='id', 
                          exclude_docs=set(), include_docs=set()):
    """
    CREATE TABLE words_info SELECT doc_bows.word_id, 
    COUNT(doc_bows.doc_id) as n_docs, 
    SUM(doc_bows.wcount) as n_total  
    FROM  doc_bows 
    GROUP BY doc_bows.word_id;
    
    """
    
    if exclude_docs or include_docs:
        if exclude_docs:
            base = "AND doc_bows.doc_id NOT IN ({}) "
            dd = exclude_docs
        elif include_docs:
            base = "AND doc_bows.doc_id IN ({}) "
            dd = include_docs
        dd = [str(int(did)) for did in dd]
        dd = ", ".join(dd)
        ie_where_text = base.format(dd)
    else:
        ie_where_text = ""
        
        
    format_strings = ', '.join(['%s'] * len(words))
    
    if wtype=='word':
        where_clause = "WHERE words.word IN ({}) ".format(format_strings)
        where_clause += ie_where_text
        query = "SELECT doc_bows.word_id, COUNT(DISTINCT doc_bows.doc_id) as n_docs, " +\
                "SUM(doc_bows.wcount) as n_total " +\
                "FROM  doc_bows LEFT JOIN words ON (doc_bows.word_id = words.id) " +\
                where_clause +\
                "GROUP BY doc_bows.word_id"
        
    elif wtype=='id':
        where_clause = "WHERE doc_bows.word_id IN ({}) ".format(format_strings)
        where_clause += ie_where_text
        query = "SELECT doc_bows.word_id, COUNT(DISTINCT doc_bows.doc_id) as n_docs, " +\
                "SUM(doc_bows.wcount) as n_total " +\
                "FROM  doc_bows " +\
                where_clause +\
                "GROUP BY doc_bows.word_id"
            
    cur.execute(query, (words))
    result = dfDocsFromCursor(cur)
    return(result)


def query_docBOW(cur, doc_id, word_list = []):
    query = "SELECT word_id, wcount FROM doc_bows WHERE doc_id = {}".format(doc_id)
    cur.execute(query)
    cols = cur.column_names
    bow = [{cols[0] : e[0], cols[1] : e[1]} for e in cur.fetchall()]
    if word_list:
        bow = [e for e in bow if e['word_id'] in word_list]
    return(bow)


def query_AllDocWords(cur, doc_ids):
    doc_ids = list(doc_ids)
    format_strings = ','.join(['%s'] * len(doc_ids))
    query = ("SELECT DISTINCT word_id "
             "FROM doc_bows "
             "WHERE doc_id IN ({})".format(format_strings))
    cur.execute(query, (doc_ids))
    words = [e[0] for e in cur.fetchall()]
    return(words)
        
    

        
if __name__=="__main__":
    
    fd = utils.get_main_dir()
    test_contents_dir = utils.os.path.join(fd,
                                           "data/interim/test_feedlinks.pkl")
    with open(test_contents_dir, 'rb') as f1:
        contents = utils.pickle.load(f1)
        
    print(len(contents))
    
    rns = saveNewLinks(contents)
                
    print(rns[:10])
