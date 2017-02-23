#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 22 20:31:42 2017

@author: immersinn
"""

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