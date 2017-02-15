#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  9 22:54:46 2017

@author: immersinn
"""


import numpy
from scipy import spatial
from bs4 import BeautifulSoup as bs


nltk_stops = set(
                   ['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours',
                    'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers',
                    'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
                    'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are',
                    'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does',
                    'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until',
                    'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into',
                    'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down',
                    'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here',
                    'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
                    'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
                    'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now']
)




def extractHTMLText(html_content):
    return(bs(html_content, 'html.parser').text.strip())


def build_text_feature(doc, components = ['title'], 
                      lower=True, remove_stops=True,
                      html_text=False):
    """
    Build simple text feature from RSS doc entries;
    default uses ONLY the title, which seems to be sufficient
    for most cases..
    """
    
    if html_text:
        text_extract = lambda x: extractHTMLText(x)
    else:
        text_extract = lambda x: x
    
    # Build base feature from components
    feature = ""
    for comp in components:
        feature += ' ' + text_extract(doc[comp])
        
    # Other preprocessing steps
    if lower:
        feature = feature.lower()
    if remove_stops:
        feature = ' '.join([w for w in feature.split() if w not in nltk_stops])
    return(feature)



def calcJMSDocScores(doc_word_vecs, 
                     query_word_vecs = numpy.empty((0,0)),
                     lambda_param=0.1, standarize_scores=True):
    
    # Build necessary elements for JM
    doc_lengths = numpy.array(doc_word_vecs.sum(axis=1)
                              ).reshape((doc_word_vecs.shape[0],1))
    
    word_probs = numpy.array(doc_word_vecs.sum(axis=0) / doc_word_vecs.sum()
                             ).reshape((doc_word_vecs.shape[1],1))
    
    weighted_doc_vecs = numpy.log(1 + (1-lambda_param) / lambda_param * \
                                  doc_word_vecs / \
                                  numpy.dot(doc_lengths, word_probs.T)
                                  )
    
    
    # Calculate the scores between queries (docs) and docs
    if query_word_vecs.shape == (0,0):
        doc_doc_scores = spatial.distance.cdist(weighted_doc_vecs, 
                                                weighted_doc_vecs,
                                                numpy.dot)
        doc_doc_scores -= numpy.diag(doc_doc_scores.diagonal())
    else:
        doc_doc_scores = spatial.distance.cdist(query_word_vecs,
                                                weighted_doc_vecs,
                                                numpy.dot)
    if standarize_scores:
        doc_doc_scores /= doc_doc_scores.max()
        
    return(doc_doc_scores)


def findEventCCs(doc_doc_scores, cutoff=0.5):
    
    # Find where Score is greater than threshold cutoff
    hits = numpy.where(doc_doc_scores > cutoff)
    
    # Initilize Variables
    unique_nodes = set()
    unique_nodes.update(set(hits[0]))
    unique_nodes.update(set(hits[1]))
    visited = set()
    connected_components = list()
    
    # Get Connected Compoentns
    for node in unique_nodes:
        
        if node not in visited:
            ccc = set([node])
            to_visit = set([node])
            
            while to_visit:
                node = to_visit.pop()
                visited.update([node])
                
                # Find all instances of node
                h0_find = numpy.where(hits[0]==node)
                h1_find = numpy.where(hits[1]==node)
    
                # Get compliments of node
                h0_newnodes = set(hits[1][h0_find])
                h1_newnodes = set(hits[0][h1_find])
    
                # Update the current connected component
                ccc.update(h0_newnodes)
                ccc.update(h1_newnodes)
    
                # Update the "to visit" list while avoiding
                # "forever" loops...
                to_visit.update(h0_newnodes.difference(visited))
                to_visit.update(h1_newnodes.difference(visited))
                
            connected_components.append(ccc)
            
    return(connected_components)


def compare_entries_v2(docs, cc):
    
    def print_doc_stats(i):
        doc = docs.ix[i]
        print(doc.published)
        print(doc.rss_link)
        print(doc.text_feature)
        
    for node in cc:
        print_doc_stats(node)
        print('\n')


if __name__=="__main__":
    
    from sklearn.feature_extraction.text import CountVectorizer
    import mysql_utils
    
    # Query Data
    cnx = mysql_utils.getCnx()
    cur = mysql_utils.getCur(cnx)
    docs = mysql_utils.query_docs_by_datetime(cur, 
                                              start_dt='2017-02-1 00:00:00',
                                              end_dt='2017-02-02 00:00:00')
    
    # Filter out duplicates?
    unique_entries = []
    titles = set()
    for i in docs.index:
        if docs.ix[i].title not in titles:
            unique_entries.append(i)
            titles.update([docs.ix[i].title])
            
    docs = docs.ix[unique_entries]
    docs.index = range(docs.shape[0])
    
    
    # Build the text feature
    docs['text_feature'] = [build_text_feature(docs.ix[i]) for i in docs.index]
    count_vect = CountVectorizer()
    X_train_counts = count_vect.fit_transform(docs.text_feature)
    
    # Calculate scores
    doc_doc_scores = calcJMSDocScores(X_train_counts)
    connected_components = findEventCCs(doc_doc_scores, cutoff=0.5)
    
    for cc in connected_components:
        compare_entries_v2(docs, cc)
        print('\n')