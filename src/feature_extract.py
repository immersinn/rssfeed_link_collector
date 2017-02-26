#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 26 08:27:07 2017

@author: immersinn
"""

from scipy import sparse

import mappers


    
class CountVecSimple:
    """
    
    """
    
    
    def __init__(self,):
        self._bwm = mappers.BOWIDMapper()
    
    
    def fit(self, bows):
        
        # "Collapse" bows
        self._bwm.fit(bows)
        
    
    def transform(self, bows):
        
        # Transform / "Collapse" the BOWS
        bows = self._bwm.transform(bows)
        
        # Build BOW Matrix; scipy.sparse.coo_matrix
        ii, jj, data = ([], [], [])
        for entry in bows:
            did, bow = entry['doc_id'], entry['bow']
            ii.extend([did for _ in range(len(bow))])
            wids = [wid for wid in bow.keys()]
            jj.extend(wids)
            data.extend([bow[wid] for wid in wids])
        bowmat = sparse.coo_matrix((data, (ii,jj)))
        
        return(bowmat)
    
    
    def fit_transform(self, bows):
        bows = self._bwm.fit_transform(bows)
        return(self.transform(bows))