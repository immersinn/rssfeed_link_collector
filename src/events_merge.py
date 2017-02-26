#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  9 22:54:46 2017

@author: immersinn
"""

import datetime

import numpy
from scipy import sparse
from sklearn.feature_extraction.text import CountVectorizer

import mysql_utils
import doc_proc
from mappers import DocIDMapper


def findEventCCs(doc_doc_scores, cutoff=0.5):
    
    """
    See "scipy.sparse.cs_graph_components" for potential speedup
        https://docs.scipy.org/doc/scipy-0.10.0/reference/generated/scipy.sparse.cs_graph_components.html
    """
    
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


def process_timeslice(docs, 
                      title_cutoff = 0.5, summary_cutoff = 0.15,
                      make_symmetric=True):
    """
    
    Leave graph as tuple of lists: (data (ii, jj))
    """
    
    # Filter
    docs = doc_proc.filter_unique_docs(docs)
    
    # Get Feature Similarity Scores
    docid_t, title_scores = doc_proc.get_doc_featurevecs(docs, features=['title'])
    docid_s, summary_scores = doc_proc.get_doc_featurevecs(docs)
    
    # Find where Score is greater than threshold cutoff
    hits_title = numpy.where(title_scores > title_cutoff)
    hits_summary = numpy.where(summary_scores > summary_cutoff)
    
    if make_symmetric:
        hits_title = (numpy.hstack([hits_title[0], hits_title[1]]),
                      numpy.hstack([hits_title[1], hits_title[0]]))
        hits_summary = (numpy.hstack([hits_summary[0], hits_summary[1]]),
                        numpy.hstack([hits_summary[1], hits_summary[0]]))
                                   
                
    
    # Build slice
    ij = (numpy.hstack([hits_title[0], hits_summary[0]]),
          numpy.hstack([hits_title[1], hits_summary[1]]))
    data = numpy.ones((len(ij[0]),))
    #time_slice = sparse.coo_matrix((data, ij), shape=summary_scores.shape)
    
    return(docid_t, {'ij':ij, 'data':data})


def process_timeslice_v2(docs,
                         details = {'title' : {'features' : ['title'], 
                                               'cutoff' : 0.5,
                                               'to_binary' : True, 'make_symmetric' : True},
                                    'summary' : {'features' : ['title', 'summary'],
                                                 'cutoff' : 0.1,
                                                 'to_binary' : False, 
                                                 'make_symmetric' : True, 'sym_func' : lambda x,y : (x+y)/2}
                                    }):
    """
    
    Leave graph as tuple of lists: (data (ii, jj))
    """
    
    out = {}
    
    # Filter
    docs = doc_proc.filter_unique_docs(docs)
    
    # Get Feature Similarity Scores
    for label in details:
        entry = details[label]
        docid, scores = doc_proc.get_doc_featurevecs(docs,
                                            features=entry['features'])
        hits = numpy.where(scores > entry['cutoff'])
        
        if entry['to_binary']:
            if entry['make_symmetric']:
                hits = (numpy.hstack([hits[0], hits[1]]),
                        numpy.hstack([hits[1], hits[0]]))
            data = numpy.ones((len(hits[0])))
        elif not entry['to_binary']:
            if entry['make_symmetric']:
                data, ii, jj = [], [], []
                for k in range(len(hits[0])):
                    i = hits[0][k]
                    j = hits[1][k]
                    val = entry['sym_func'](scores[i,j], scores[j,i])
                    data.extend([val, val])
                    ii.extend([i,j])
                    jj.extend([j,i])
                hits = (numpy.array(ii),
                        numpy.array(jj)
                       )
                data = numpy.array(data)
            else:
                data = scores(hits[0], hits[1])
                
        out[label] = {'doc_ids' : docid,
                      'tslice' : {
                                  'vals' : data, 
                                  'ij' : hits
                                 }
                      }
        
    return(out)


def get_slices(cursor, start_date, n_segments, spacing_hours=6, span_segments=4):
    
    # Prelims
    details ={'summary' : {'features' : ['title', 'summary'],
                       'cutoff' : 0.1,
                       'to_binary' : False,
                       'make_symmetric' : True, 'sym_func' : lambda x,y : (x+y)/2}
         }
    
    # Configure datetimes
    if len(start_date) == 10:
        start_date += " 00:00:00"
        
    base = datetime.datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
    date_list = [base + datetime.timedelta(hours=x) \
                 for x in range(0, 
                                (((n_segments - 1) + span_segments) * spacing_hours) + 1,
                                spacing_hours)]
                 
    # Query data
    docids = {}
    tslices = {}
    for i in range(len(date_list)-span_segments):
        out_01 = process_timeslice_v2(mysql_utils.query_docs_by_datetime(cursor=cursor,
                                                                         start_dt=date_list[i],
                                                                         end_dt=date_list[i + span_segments]),
                                      details=details)
        docids[i] = out_01['summary']['doc_ids']
        tslices[i] = out_01['summary']['tslice']
        
    return(docids, tslices)


def merge_slices_simple(docids, tslices, connected_pairs):
    """
    "Simple Stack" of the multiple time-slices; that is, just 
    make one ol' big network from the slices where identical stories
    are the same node in the network, no multiplex
    
    "By default when converting to CSR or CSC format, duplicate (i,j) entries 
    will be summed together. This facilitates efficient construction of finite 
    element matrices and the like. (see example)"
    """
    
    # Get the set of unique ids and map docs ids to these
    idmapper = DocIDMapper()
    idmapper.fit([v for v in docids.values()])
    docids = {k : idmapper.transform(val) for k,val in docids.items()}
    
    # Find matching entries in the slices
    s2smap = {}
    for pair in connected_pairs:
        temp = []
        for i,did in enumerate(docids[pair[1]]):
            try:
                temp.append((docids[pair[0]].index(did), i))
            except ValueError:
                pass
        s2smap['-'.join([str(p) for p in pair])] = temp
              
    # Create the big graph
    newi = []
    newj = []
    newdata = []
    for k,ts in tslices.items():
        newi.extend([docids[k][ent] for ent in ts['ij'][0]])
        newj.extend([docids[k][ent] for ent in ts['ij'][1]])
        newdata.extend(ts['vals'])
    bg = sparse.coo_matrix((newdata, (newi, newj)),
                           shape=(len(idmapper), len(idmapper)))
    
    return(bg, idmapper)


if __name__=="__main__":
    
    import metrics
        
    # Query Data
    cnx = mysql_utils.getCnx()
    cur = mysql_utils.getCur(cnx)
    docs = mysql_utils.query_docs_by_datetime(cur, 
                                              start_dt='2017-02-1 00:00:00',
                                              end_dt='2017-02-02 00:00:00')
    
    # Filter out duplicates?
    docs = doc_proc.filter_unique_docs(docs)
    
    
    # Build the text feature
    docs['text_feature'] = [doc_proc.build_text_feature(docs.ix[i]) for i in docs.index]
    count_vect = CountVectorizer()
    X_train_counts = count_vect.fit_transform(docs.text_feature)
    
    # Calculate scores
    doc_doc_scores = metrics.calcJMSDocScores(X_train_counts)
    connected_components = findEventCCs(doc_doc_scores, cutoff=0.5)
    
    for cc in connected_components:
        compare_entries_v2(docs, cc)
        print('\n')