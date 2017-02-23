#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 22 10:36:35 2017

@author: immersinn
"""


import mysql_utils


def place_holdeR():
    
    
    # Get mysql connection, cursor
    cnx = mysql_utils.getCnx()
    cur = mysql_utils.getCur(cnx)
    
    
    for tps in time_periods:
        docs = mysql_utils.query_docs_by_datetime(cursor=cursor,
                                                  start_dt=time_period['start'],
                                                  end_dt=time_period['end'])
        
        
class JMSmooth:
    
    def __init__(self,):
        pass
    
    
    def fit(self, doc_word_vectors,):
        pass
        # Build the vocab
        # Calculate the word probs
        # Count
    
    
    def update(self, doc_word_vectors,):
        pass
    
    
    def transform(self, queries):
        pass