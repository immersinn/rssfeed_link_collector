#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 26 08:24:04 2017

@author: immersinn
"""


class WordIDMapper:
    """
    
    """
    
    def __init__(self,):
        self._wids = set()
        self.wid2gid = {}
        self.gid2wid = {}
        
        
    def __len__(self,):
        return(len(self._wids))


    def fit(self, wid_list):
        word_ids = set(wid_list)
        self.wid2gid = {wid : i for i,wid in enumerate(word_ids)}
        self.gid2wid = {i : wid for i,wid in enumerate(word_ids)}
        self._wids = word_ids
        
        
    def transform(self, wids_list):
        wids_list = [[self.wid2gid[wid] for wid in wids] for wids in wids_list]
        return(wids_list)
    
    
    def transform_one(self, wid):
        return(self.wid2gid[wid])
    
    
    def fit_transform(self, wid_list):
        self.fit(wid_list)
        return(self.transform(wid_list))
    

    def update(self, wid_list):
        for wid in wid_list:
            if wid not in self._wids:
                self._wids.update([wid])
                self.wid2gid[wid] = len(self.wid2gid)
                self.gid2wid[len(self.gid2wid)] = wid
                    
                    

class DocIDMapper:
    """
    
    """
    
    def __init__(self,):
        self._docids = set()
        self.did2gid = {}
        self.gid2did = {}
        
        
    def __len__(self):
        return(len(self._docids))
    
    
    def fit(self, did_list):
        if type(did_list[0]) in [tuple, list]:
            did_list = [d for did in did_list for d in did]
        doc_ids = set(did_list)
        self.did2gid = {did : i for i,did in enumerate(doc_ids)}
        self.gid2did = {i : did for i,did in enumerate(doc_ids)}
        self._docids = doc_ids
        
    
    def transform(self, did_list):
        out = []
        for did in did_list:
            try:
                out.append(self.did2gid[did])
            except KeyError:
                out.append(None)
        return(out)
    
    
    def transform_one(self, did):
        return(self.did2gid[did])
    
    
    def fit_transform(self, did_list):
        self.fit(did_list)
        return(self.transform(did_list))


class BOWIDMapper:
    """
    
    """
    
    def __init__(self,):
        self.docid_map = DocIDMapper()
        self.wordid_map = WordIDMapper()
        
    
    def _fit_wordids(self, bows_only):
        wids_list = set()
        for bow in bows_only:
            wids_list.update(set([wid for wid in bow.keys()]))
        wids_list=  list(wids_list)
        self.wordid_map.fit(wids_list)
        
        
    def _transform_bow_wordids(self, bow_only):
        return({self.wordid_map.transform_one(wid) : wcount \
                for wid,wcount in bow_only.items()})
        
        
    def fit(self, bows):
        self.docid_map.fit([e['doc_id'] for e in bows])
        self._fit_wordids([e['bow'] for e in bows])
        
        
    def transform(self, bows):
        bows = [{'doc_id' : self.docid_map.transform_one(bow['doc_id']),
                 'bow' : self._transform_bow_wordids(bow['bow'])} \
                for bow in bows]
        return(bows)
    
    
    def transform_one(self, bow):
        return({'doc_id' : self.docid_map.transform_one(bow['doc_id']),
                'bow' : self._transform_bow_wordids(bow['bow'])
                }
               )
    
    
    def lookup_docid(self, did):
        try:
            return(self.docid_map.did2gid[did])
        except KeyError:
            err_msg = "Not a valid doc_id"
            raise KeyError(err_msg)
            
    def lookup_wordid(self, wid):
        try:
            return(self.wordid_map.wid2gid[wid])
        except KeyError:
            err_msg = "Not a valid word_id"
            raise KeyError(err_msg)
            
    
    def revlookup_docid(self, dgid):
        try:
            return(self.docid_map.gid2did[dgid])
        except KeyError:
            err_msg = "Not a valid mapped doc_id"
            raise KeyError(err_msg)
            
            
    def revlookup_wordid(self, wgid):
        try:
            return(self.wordid_map.gid2wid[wgid])
        except KeyError:
            err_msg = "Not a valid mapped word_id"
            raise KeyError(err_msg)
