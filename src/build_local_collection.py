#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 23 22:06:12 2017

@author: immersinn
"""

import mysql_utils
import doc_proc
import init_tdm_tables


def ids2ints(id_series):
    return([int(i) for i in list(id_series)])


def get_localWordsAndDocs(doc,
                          l01_ndoc_cutoff=100,
                          l02_restrict={'n_docs_bg': {
                                                      'max' : 50
                                                      },
                                        'n_docs_qw' : {
                                                       'min' : 3
                                                       },
                                        'ratio' : 2
                                        },
                          verbose=False):
    
    if verbose:
        print('Init-ing tools...')
    

    # Doc Proc Stuffs
    dd = lambda doc: doc_proc.build_text_feature(doc, 
                                                 components = ['title', 'summary'],
                                                 lower=False, 
                                                 remove_stops=False,
                                                 html_text=True,
                                                 )
    dp = init_tdm_tables.DocProcessor()
    stops = doc_proc.nltk_stops
    stops_lookup = mysql_utils.query_wordIDLookup(stops)
    n_docs_tot = mysql_utils.query_totalEntries('rssfeed_links')
    
    
    # Level 0
    if verbose:
        print('Starting Level 0...')
    bow = dp.doc2BOW(dd(doc))
    orig_query_words = [w for w in \
                       (mysql_utils.query_wordIDLookup([w for w in bow if \
                                                        w not in doc_proc.nltk_stops])).keys()
                       ]
    
    
    # Level 1
    if verbose:
        print('Starting Level 1...')
    ##ndoc_cutoff = 100
    word_count_info = mysql_utils.query_wordSummaryInfo(orig_query_words, wtype='id')
    qw_l01 = ids2ints(word_count_info[word_count_info.n_docs < l01_ndoc_cutoff].word_id)
    docs_l01, wcs_l01 = mysql_utils.query_docsOnWords(qw_l01, word_type='id')

    
    # Level 2
    if verbose:
        print('Starting Level 2...')
    query_words = mysql_utils.query_AllDocWords(docs_l01)
    query_words = [w for w in query_words if w not in stops_lookup.keys()]
    
    bgwi = mysql_utils.query_backgroundWordInfo(query_words)
    bgwi['frac'] = bgwi.n_docs / n_docs_tot
    qwwi = mysql_utils.query_wordSummaryInfo(query_words,
                                             wtype='id', include_docs=docs_l01)
    qwwi['frac'] = qwwi.n_docs / len(docs_l01)
    wi = bgwi.join(qwwi, on=['word_id'], lsuffix='_bg', rsuffix='_qw')
    wi['ratio'] = wi.frac_qw / wi.frac_bg
    
    # Restrict query words based on "words_info" table in mysql
    # Say, more than 5 docs, but less than 100 (50) (20) docs?
    word_filter_l02 = lambda x: (x['n_docs_qw'] >= 3 and x['n_docs_bg'] < 50 and x['ratio'] > 2)
    qw_l02 = ids2ints(wi.word_id_bg[wi.apply(lambda entry: word_filter_l02(entry), axis=1)])
    docs_l02, wcs_l02 = mysql_utils.query_docsOnWords(qw_l02,
                                                      word_type="id", 
                                                      exclude_docs=docs_l01)

    
    # Collect info and return data
    if verbose:
        print('Collecting data, getting BOWs and finishing up...')
    words = {'orig' : set(orig_query_words),
             'l01' : set(qw_l01),
             'l02' : set(qw_l02)
             }
    docs = {'orig' : doc,
            'l01' : docs_l01,
            'l02' : docs_l02}

    return(docs, words, bow)
    


if __name__=="__main__":
    
    """
    doc_url = "http://www.cnn.com/2017/02/23/politics/fbi-refused-white-house-request-to-knock-down-recent-trump-russia-stories/index.html"
    """
    
    print("Starting process...")
    
    doc = {"title" : "FBI refused White House request to knock down recent Trump-Russia stories",
           "summary" : "Washington (CNN) The FBI rejected a recent White House request to publicly knock down media reports about communications between Donald Trump's associates and Russians known to US intelligence during the 2016 presidential campaign, multiple US officials briefed on the matter tell CNN."}
    print('Doc title:')
    print('"""' + doc['title'] + '"""')
    
    docs, words, orig_bow = get_localWordsAndDocs(doc, verbose=True)
    
    # Gen BOWs
    bows = [{'doc_id' : 'orig', 'bow' : orig_bow}]
    for d in docs['l01']:
        bows.append({'doc_id' : d,
                     'bow' : mysql_utils.query_docBOW(d, word_list=words)})
    for d in docs['l02']:
        bows.append({'doc_id' : d,
                     'bow' : mysql_utils.query_docBOW(d, word_list=words)})
    
    print('Total documents found: {}'.format(len(bows)))
    print('Total words to be used: {}'.format(sum([len(words[w]) for w in words])))
    
    print('fine')