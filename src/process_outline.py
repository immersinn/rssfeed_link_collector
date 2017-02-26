#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 26 09:55:40 2017

@author: immersinn
"""

import numpy

import build_local_collection
import mysql_utils
from feature_extract import CountVecSimple
import metrics
import spectral_partition


def main(doc):

    """
    
    00: doc = {Get a story}
    01: docs, words = build_local_collection.get_localWordsAndDocs(doc)
    02: bows = TBD(docs, words)
    03: bow_mat = CountVecSimple.fit_transform()
    04: dds = metrics.calcJMSDocScores(bow_mat)
    05: Do Work
        A: JM Smooth Simple:
            i) close_docs = numpy.argsort(dds[orig_index,:], )[-20:]
        B: Spectral Graph (Simple)
            i)    dds_sym = (dds + dds.T) / 2
            ii)   C,M = spectral_partition.spectralGraphPartitionSingle(dds_sym, L=6.)
            iii)  orig_grp = numpy.where(C == C[orig_index])[0]
    06: Analysis
        A: doc_info = mysql_utils.query_docsDetails(cur, grp)
    """
    
    # Get Local Collection
    docs, words, orig_bow = build_local_collection.get_localWordsAndDocs(doc)
    
    
    # Gen BOWs
    bows = [{'doc_id' : 'orig', 'bow' : orig_bow}]
    for d in docs['l01']:
        bows.append({'doc_id' : d,
                     'bow' : mysql_utils.query_docBOW(d, word_list=words)})
    for d in docs['l02']:
        bows.append({'doc_id' : d,
                     'bow' : mysql_utils.query_docBOW(d, word_list=words)})
    
    #
    cvs = CountVecSimple()
    bow_mat = cvs.fit_transform(bows)
    orig_index = cvs._bwm.lookup_docid('orig')
    
    #
    dds = metrics.calcJMSDocScores(bow_mat)
    
    # JMS
    jms_close_docs = numpy.argsort(dds[orig_index,:], )[-20:]
    jms_close_docs = [cvs._bwm.revlookup_docid(did) for did in jms_close_docs]
    
    # Spectral
    dds_sym = (dds + dds.T) / 2
    C,M = spectral_partition.spectralGraphPartitionSingle(dds_sym, L=6.)
    orig_grp = numpy.where(C == C[orig_index])[0]
    orig_grp = [cvs._bwm.revlookup_docid(did) for did in orig_grp]
    _ = orig_grp.remove('orig')
    
    
    # retrieve docs
    jms_doc_info = mysql_utils.query_docsDetails(jms_close_docs)
    spec_doc_info = mysql_utils.query_docsDetails(orig_grp)