#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 22 12:04:55 2017

@author: immersinn
"""

import spacy
from spacy import attrs
import textacy

import mysql_utils


class DocProcessor():
    
    def __init__(self,):
        preproc = lambda text: textacy.preprocess.preprocess_text(text,
                                                                  no_contractions=True,
                                                                  no_numbers=True,
                                                                  no_emails=True
                                                                  )
        nlp = spacy.load("en", add_vectors=False)
        nlp.pipeline = [nlp.tagger, nlp.parser]
        
        self.preproc = preproc
        self._nlp = nlp
        self.pipe = self._nlp.pipe
    
    
    def doc2BOW(self, doc):
        return(self._bow_transform(doc))
    
    
    def _bow_transform(self, doc):
        doc = self.preproc(doc)
        doc = self.pipe(doc)
        bow = {self._nlp.vocab[k].lower_ : v \
               for k,v in doc.count_by(attrs.LOWER).items()}
        return(bow)


class TDMTHandle():
    
    def __init__(self,):
        self.cnx = mysql_utils.getCnx()
        self.cur = mysql_utils.getCur(self.cnx)
        
    def intsertDocBOW(self, doc):
        pass
    

def process_docs(limit=100):
    
    # Initialize helper classes
    dp = DocProcessor()
    th = TDMTHandle()
    
    # Initilize MySQL con for query, query
    cnx = mysql_utils.getCnx()
    cur = mysql_utils.getCur(cnx)
    
    query_text = '''SELECT id, title, summary FROM %s LIMIT %s'''
    cur.execute(query_text, (mysql_utils.TABLE, limit))
    
    # Iterate over docs
    for doc in cur:
        bow = dp.doc2BOW(doc)
        th.insertDocBOW(bow)
        
    # Close connection 
    cnx.close()
        