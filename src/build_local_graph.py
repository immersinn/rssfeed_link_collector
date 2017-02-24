#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 23 22:06:12 2017

@author: immersinn
"""

import numpy
import scipy
import pandas

import mysql_utils
import doc_proc
import init_tdm_tables


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


def query_docsOnWords(cur, words, word_type="word", exclude_docs=set()):
    
    if word_type == "word":
        word_doc_query = ("SELECT doc_bows.doc_id, doc_bows.wcount "
                          "FROM  doc_bows LEFT JOIN words ON (doc_bows.word_id = words.id) "
                          "WHERE words.word = '{}'")
    elif word_type == "id":
        word_doc_query = ("SELECT doc_bows.doc_id, doc_bows.wcount "
                          "FROM  doc_bows LEFT JOIN words ON (doc_bows.word_id = words.id) "
                          "WHERE words.id = '{}'")

    doc_ids = set()
    word_count_store = []
    for word in words:
        cur.execute(word_doc_query.format(word))
        result = mysql_utils.dfDocsFromCursor(cur)
        result = result[[i not in exclude_docs for i in result['doc_id']]]
        if result.shape[0] > 0:
            doc_ids.update(set(result['doc_id']))
            word_count_store.append({'word' : word,
                                     'n_docs' : result.shape[0],
                                     'n_tot' : result['wcount'].sum()})

    doc_ids = [int(i) for i in doc_ids]
    word_count_store = pandas.DataFrame(word_count_store)
        
    return(doc_ids, word_count_store)


def word_summary_info(cur, words, wtype='id', exclude_docs=set()):
    
    if exclude_docs:
        exclude_docs = [str(int(did)) for did in exclude_docs]
        exclude_docs = ", ".join(exclude_docs)
        exclude_where_text = "AND doc_bows.doc_id NOT IN ({}) ".format(exclude_docs)
        
    format_strings = ', '.join(['%s'] * len(words))
    
    if wtype=='word':
        where_clause = "WHERE words.word IN ({}) ".format(format_strings)
        if exclude_docs:
            where_clause += exclude_where_text
        query = "SELECT doc_bows.word_id, COUNT(doc_bows.doc_id) as n_docs, SUM(doc_bows.wcount) as n_total " +\
                 "FROM  doc_bows LEFT JOIN words ON (doc_bows.word_id = words.id) " +\
                 where_clause +\
                 "GROUP BY doc_bows.word_id"
        
    elif wtype=='id':
        where_clause = "WHERE doc_bows.word_id IN ({}) ".format(format_strings)
        if exclude_docs:
            where_clause += exclude_where_text
        query = "SELECT doc_bows.word_id, COUNT(doc_bows.doc_id) as n_docs, SUM(doc_bows.wcount) as n_total " +\
                 "FROM  doc_bows " +\
                 where_clause +\
                 "GROUP BY doc_bows.word_id"
            
    cur.execute(query, (words))
    result = mysql_utils.dfDocsFromCursor(cur)
    return(result)


def query_docBOW(cur, doc_id):
    query = "SELECT word_id, wcount FROM doc_bows WHERE doc_id = {}".format(doc_id)
    cur.execute(query)
    cols = cur.column_names
    bow = [{cols[0] : e[0], cols[1] : e[1]} for e in cur.fetchall()]
    return(bow)


def query_AllDocWords(cur, doc_ids):
    format_strings = ','.join(['%s'] * len(doc_ids))
    query = ("SELECT DISTINCT word_id "
             "FROM doc_bows "
             "WHERE doc_id IN ({})".format(format_strings))
    cur.execute(query, (doc_ids))
    words = [e[0] for e in cur.fetchall()]
    return(words)


def main(doc):
    
    # Connections
    cnx = mysql_utils.getCnx()
    cur = mysql_utils.getCur(cnx)
    
    # Doc Proc Stuffs
    dd = lambda doc: doc_proc.build_text_feature(doc, 
                                                 components = ['title', 'summary'],
                                                 lower=False, 
                                                 remove_stops=False,
                                                 html_text=True,
                                                 )
    dp = init_tdm_tables.DocProcessor()
    stops = doc_proc.nltk_stops
    stops_lookup = query_wordIDLookup(cur, stops)
    
    
    # Level 0:
    bow = dp.doc2BOW(dd(doc))
    query_words = [w for w in bow if w not in stops]
    
    
    # Level 1:
    ndoc_cutoff = 100
    word_count_info = word_summary_info(cur, query_words, wtype='word')
    qw_l01 = [int(w) for w in list(word_count_info[word_count_info.n_docs < ndoc_cutoff].word_id)]
    docs_l01, wcs_l01 = query_docsOnWords(cur, qw_l01, word_type='id')

    
    # Level 2
    query_words = query_AllDocWords(cur, docs_l01)
    query_words = [w for w in query_words if w not in stops_lookup.keys()]
    word_count_info = word_summary_info(cur, query_words,
                                        wtype='id', exclude_docs=docs_l01)
    
    ndoc_cutoff_l2 = 20
    qw_l02 = [int(w) for w in list(word_count_info[word_count_info.n_docs < ndoc_cutoff_l2].word_id)]
    docs_l02, wcs_l02 = query_docsOnWords(cur, qw_l02,
                                          word_type="id", exclude_docs=docs_l01)
    