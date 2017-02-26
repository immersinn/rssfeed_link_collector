#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 26 08:15:55 2017

@author: immersinn
"""

import numpy
from scipy import spatial


def calcJMSDocScores(doc_word_vecs, 
                     query_word_vecs = numpy.empty((0,0)),
                     lambda_param=0.1, standarize_scores=True):
    
    ## MAYBE UPDATE TO USE SPARSE BY DEFAULT, UNLESS < MAX_SIZE??
    
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