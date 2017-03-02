#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 28 18:47:18 2017

@author: immersinn
"""

import numpy
import pandas

import mysql_utils
import feature_extract
import metrics
import spectral_partition
import graph_plot_utils


def build_doc_score_info_table(score_matrix, group, story_index, id_lookup, 
                               doc_fields=('id', 'link', 'title', 'summary', 'published')):
    
    
    # Get the score for the member of "group" from the score_matrix
    scores = [{'id': did, 'score' : score_matrix[story_index,
                                                 id_lookup.lookup_docid(did)]} for did in group]
    scores = pandas.DataFrame(scores)
    scores.index = scores['id']
    scores = scores[['score']]
    
    # Query the document info
    doc_score_info_table = mysql_utils.query_docsDetails(group, fields=doc_fields)

    # Merge DFs and sort on score
    doc_score_info_table.index = doc_score_info_table['id']
    columns = list(doc_score_info_table.columns)
    columns.remove('id')
    doc_score_info_table = doc_score_info_table[columns]
    doc_score_info_table = doc_score_info_table.join(scores)
    doc_score_info_table = doc_score_info_table.sort_values(by='score', ascending=False)
    
    return(doc_score_info_table)


def get_jms_best(scores_matrix, story_index, id_lookup, cutoff=0, n=20):

    
    if cutoff > 0:
        best_doc_ids = numpy.where(scores_matrix[story_index,:] >= cutoff)[0]
    else:
        best_doc_ids = numpy.argsort(scores_matrix[story_index,:], )[-n:]
    best_doc_ids = [id_lookup.revlookup_docid(did) for did in best_doc_ids]
    if 'orig' in best_doc_ids:
        best_doc_ids.remove('orig')
    
    best_docs_info = build_doc_score_info_table(scores_matrix, 
                                                best_doc_ids, story_index,
                                                id_lookup)
    
    return({'docs_info' : best_docs_info})



def convert_g(A, groups, cci_lookup, id_lookup, cutoff=0.1):
    
    
    # Get vertices
    verts = [{'id' : id_lookup.revlookup_docid(cci_lookup[did]),
              'name' : str(did),
              'group' : groups[did]} \
            for did in range(A.shape[0])]
    qds = [did['id'] for did in verts if did['id'] != 'orig']
    titles = mysql_utils.query_docsDetails(qds, fields=['id', 'title'])
    indx_map = {v :i for i,v in enumerate(list(titles['id']))}
    for did in verts:
        if did['id'] != 'orig':
            did['label'] = titles.ix[indx_map[did['id']]]['title']
        else:
            did['label'] = 'Original Doc'
    
    
    # Get Edges
    edges = (numpy.where(A > cutoff))
    edges = [{'from' : str(e[0]), 'to' : str(e[1]), 'weight' : 20*A[e[0], e[1]]} \
             for e in zip(list(edges[0]), list(edges[1]))]
    
    
    g = graph_plot_utils.create_igraph(verts, edges,
                                       vert_attrs=['name', 'label', 'group'],
                                       edge_attrs=['weight'])
    
    return(g)



def get_spectral_best(scores_matrix, story_index, id_lookup,
                      method='23recur', Bin='bNG', L=1., min_grp_size=4,
                      graph_edge_cutoff=0.1,):
    
    # Get only connected component
    ##scores_matrix_2 = (scores_matrix + scores_matrix.T) / 2
    cci = numpy.where(scores_matrix.sum(axis=1) > 0)[0]
    cci_lookup = {i : v for i,v in enumerate(cci)}
    scores_matrix = scores_matrix[cci,:][:, cci]
    
    if method=='23recur':
        groups, counts, history = spectral_partition.spectralGraphPartition23(A=scores_matrix,
                                                                              Bin=Bin,
                                                                              L=L, 
                                                                              n_cutoff=min_grp_size)
        
    best_doc_ids = numpy.where(groups == groups[story_index])[0]
    best_doc_ids = [cci_lookup[did] for did in best_doc_ids]
    best_doc_ids = [id_lookup.revlookup_docid(did) for did in best_doc_ids]
    if 'orig' in best_doc_ids:
        best_doc_ids.remove('orig')
    
    best_docs_info = build_doc_score_info_table(scores_matrix, 
                                                best_doc_ids, story_index,
                                                id_lookup)
    g = convert_g(scores_matrix, groups, cci_lookup, id_lookup,
                  cutoff=graph_edge_cutoff)
    
    return({'docs_info' : best_docs_info,
            'igraph' : g,
            'A' : scores_matrix,
            'cluster_info' : (groups, counts, history)})


def compare_methods(docs, words, bow,
                    scoring_metric = metrics.calcJMSDocScores,
                    cutoff=0.15,
                    L=2, min_grp_size=15, graph_edge_cutoff=0.1,
                    use_orig_bow_words=True,
                    verbose=False):
    
    if verbose:
        print('Collecting words and creating BOWS...')
    
    
    # Define set of Word to use
    words_all = set()
    if use_orig_bow_words:
        words_all.update(bow.keys())
    words_all.update(words['l01'])
    words_all.update(words['l02'])
    
    
    # Retrieve Document BOWs
    bows = [{'doc_id' : 'orig', 'bow' : {w : bow[w] for w in set(bow.keys()).intersection(words_all)}}]
    for d in docs['l01']:
        bows.append({'doc_id' : d,
                     'bow' : mysql_utils.query_docBOW(d, word_list=words_all)})
    for d in docs['l02']:
        bows.append({'doc_id' : d,
                     'bow' : mysql_utils.query_docBOW(d, word_list=words_all)})
    
    
    # Fit CountVecSimple
    cvs = feature_extract.CountVecSimple()
    cvs.fit(bows)
    orig_indx = cvs._bwm.lookup_docid('orig')
    
    
    # Calculate the scores matrix
    if verbose:
        print('Calculating scores ...')
    
    bows_matrix = cvs.transform(bows)
    scores_matrix = scoring_metric(bows_matrix)

    
    # Get best documents from various methods
    if verbose:
        print('Finding best docs...')
    
    results = {}
    if verbose:
        print('\tJMS Method...')
    results['jms_score'] = get_jms_best(scores_matrix, orig_indx, cvs._bwm,
                                        cutoff=cutoff)
    if verbose:
        print('\tSpectral Method...')
    results['spectral'] = get_spectral_best(scores_matrix, orig_indx, cvs._bwm,
                                            L=L, min_grp_size=min_grp_size,
                                            graph_edge_cutoff=graph_edge_cutoff)
    return(results)
    