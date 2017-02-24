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
import doc_proc


class DocProcessor():
    
    def __init__(self,):
        preproc = lambda text: textacy.preprocess.preprocess_text(text,
                                                                  fix_unicode=True,
                                                                  transliterate=True,
                                                                  no_contractions=False,
                                                                  no_numbers=True,
                                                                  no_phone_numbers=True,
                                                                  no_emails=True,
                                                                  no_urls=True,
                                                                  no_punct=True,
                                                                  )
        nlp = spacy.load("en", add_vectors=False)
        nlp.pipeline = [nlp.tagger, nlp.parser]
        
        self.preproc = preproc
        self._nlp = nlp
        self.process = self._nlp.make_doc
    
    
    def doc2BOW(self, doc):
        return(self._bow_transform(doc))
    
    
    def _bow_transform(self, doc):
        doc = self.preproc(doc)
        doc = self.process(doc)
        bow = {self._nlp.vocab[k].lower_ : v \
               for k,v in doc.count_by(attrs.LOWER).items()}
        return(bow)


class TDMTHandle():
    
    def __init__(self,):
        self.cnx = mysql_utils.getCnx()
        self.cur = mysql_utils.getCur(self.cnx)
        
    def insertDocBOW(self, bow, doc_id):
    
        for word in bow:
            try:
                # Step 01:
                    # insert word if new
                    # get word key
                word_id = self._word_get_key(word)
                
                # Step 02:
                    # insert counts
                self._insert_count(doc_id, word_id, bow[word])
                    
            except mysql_utils.ProgrammingError:
                self.cnx.rollback()
            except mysql_utils.IntegrityError:
                self.cnx.rollback()
            
    def _word_get_key(self, word):
        
        word_query = """SELECT id FROM words WHERE word = '{}' LIMIT 1""".format(word)
        self.cur.execute(word_query)
        key = self.cur.fetchone()
        
        if not key:
            word_insert = """INSERT INTO words (word) VALUES ('{}')""".format(word)
            self.cur.execute(word_insert)
            self.cnx.commit()
            self.cur.execute(word_query)
            key = self.cur.fetchone()
            
        key = key[0]
            
        return(key)

    
    def _insert_count(self, doc_id, word_id, count):
        count_insert = ("INSERT INTO doc_bows "
                        "(word_id, doc_id, wcount) "
                        "VALUES ({0}, {1}, {2})".format(word_id, doc_id, count)
                       )
        self.cur.execute(count_insert)
        self.cnx.commit()


def process_docs(limit=100):
    
    status = 0
    print("Prepping workspace...")
    # Initialize helper classes
    dd = lambda doc: doc_proc.build_text_feature(doc, 
                                                 components = ['title', 'summary'],
                                                 lower=False, 
                                                 remove_stops=False,
                                                 html_text=True,
                                                 )
    dp = DocProcessor()
    th = TDMTHandle()
    
    # Initilize MySQL con for query, query
    cnx = mysql_utils.getCnx()
    cur = mysql_utils.getCur(cnx)
    
    try:
    
        # Get ids for docs that have already been processed
        distint_doc_query = "SELECT DISTINCT doc_id FROM doc_bows"
        cur.execute(distint_doc_query)
        old_dids = set([entry[0] for entry in cur])
        
        
        print("Querying docs...")
        if limit > -1:
            query_text = '''SELECT id, title, summary FROM {} LIMIT {}'''.format(mysql_utils.TABLE, limit)
        elif limit == -1:
            query_text = '''SELECT id, title, summary FROM {}'''.format(mysql_utils.TABLE)
        cur.execute(query_text)
        
        
        print("Processing docs...")
        # Iterate over docs
        count = 0
        while True:
            
            try:
                if count % 250 == 0:
                    print("Processing doc {}".format(count))
                count += 1
                
                doc_dict = mysql_utils.dictDocFromCursor(cur)
                doc_id = doc_dict['id']
                
                if doc_id not in old_dids:
                    doc = dd(doc_dict)
                    bow = dp.doc2BOW(doc)
                    th.insertDocBOW(bow, doc_id)
                
            except StopIteration:
                break
            
            except KeyboardInterrupt:
                raise KeyboardInterrupt
                
        status = 1
    
            
    finally:
        # Close connection
        th.cnx.close()
        cnx.close()
        return(status)
        
    
if __name__ == "__main__":
    status = 0
    while status < 1:
        try:
            status = process_docs(limit=-1)
        except KeyboardInterrupt:
            status = 444
        except (ConnectionRefusedError, ConnectionResetError, ConnectionError):
            print("Restarting process due to connection error...")
    print(status)