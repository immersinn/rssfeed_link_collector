#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  9 22:54:46 2017

@author: immersinn
"""

import datetime

import numpy
from scipy import spatial, sparse
from sklearn.feature_extraction.text import CountVectorizer
from bs4 import BeautifulSoup as bs

import mysql_utils


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

blog_stops = set(
                 ['wired', 'physorg', 'ft', 'cnn']
                 )


def filter_unique_docs(docs):
    # Filter out duplicates?
    unique_entries = []
    titles = set()
    for i in docs.index:
        if docs.ix[i].title not in titles:
            unique_entries.append(i)
            titles.update([docs.ix[i].title])
    
    docs = docs.ix[unique_entries]
    docs.index = range(docs.shape[0])
    
    return(docs)



def extractHTMLText(html_content):
    return(bs(html_content, 'html.parser').text.strip())


def build_text_feature(doc, components = ['title'], 
                      lower=True, 
                      remove_stops=True, stops=set(),
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
        feature = ' '.join([w for w in feature.split() if w not in stops])
    return(feature)



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
        
        
def get_doc_featurevecs(docs, features=['title', 'summary']):
    # currently using link as index; fix this shit...
    
    stopwords = nltk_stops.copy()
    stopwords.update(blog_stops)
    
    # Prep features
    if 'summary' in features:
        html_text = True
    else:
        html_text = False
    ind, feature = zip(*[(docs.ix[i]['link'], 
                          build_text_feature(docs.ix[i],
                                             components=features,
                                             html_text=html_text,
                                             )) \
                         for i in docs.index]
                       )
    
    # Create count vec
    count_vect = CountVectorizer()
    X_train_counts = count_vect.fit_transform(feature)
    
    # Calculate scores
    doc_doc_scores = calcJMSDocScores(X_train_counts)
    
    return(ind, doc_doc_scores)


def process_timeslice(docs, 
                      title_cutoff = 0.5, summary_cutoff = 0.15,
                      make_symmetric=True):
    """
    
    Leave graph as tuple of lists: (data (ii, jj))
    """
    
    # Filter
    docs = filter_unique_docs(docs)
    
    # Get Feature Similarity Scores
    docid_t, title_scores = get_doc_featurevecs(docs, features=['title'])
    docid_s, summary_scores = get_doc_featurevecs(docs)
    
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
    docs = filter_unique_docs(docs)
    
    # Get Feature Similarity Scores
    for label in details:
        entry = details[label]
        docid, scores = get_doc_featurevecs(docs,
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


class DocIDMapper():
    
    def __init__(self,):
        self.uids = set()
    
    def __len__(self):
        return(len(self.uids))
    
    def _update_ids(self, docids):
        self.uids.update(set(docids))
    
    def fit(self, docids):
        if type(docids[0]) in [tuple, list]:
            for dids in docids:
                self._update_ids(dids)
        else:
            self._update_ids(docids)
            
        self.lookup = {v : i for i,v in enumerate(self.uids)}
        self.revlu = {i : v for i,v in enumerate(self.uids)}
        
    def transform(self, docids):
        out = []
        for did in docids:
            try:
                out.append(self.lookup[did])
            except KeyError:
                out.append(None)
        return(out)


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
        
    # Query Data
    cnx = mysql_utils.getCnx()
    cur = mysql_utils.getCur(cnx)
    docs = mysql_utils.query_docs_by_datetime(cur, 
                                              start_dt='2017-02-1 00:00:00',
                                              end_dt='2017-02-02 00:00:00')
    
    # Filter out duplicates?
    docs = filter_unique_docs(docs)
    
    
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