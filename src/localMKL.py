#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 22 11:09:31 2017

@author: immersinn
"""

import numpy
import scipy


def local_mKL(start_nodes, A, L):
    
    # Some prelims
    n = A.shape[0]
    k = numpy.array(A.sum(axis=1))
    kk2m = ((k * k) / k.sum() * L).reshape((n,))
    
    score = 0
    score_prev = -999
    num_iter = 0
    group = start_nodes
    
    while score > score_prev:
        
        score_prev = score
        num_iter += 1
        candidates = [i for i in group]
        new_cands = set(A[candidates,:].nonzero()[1])
        candidates = set(candidates)
        candidates = candidates.update(new_cands)
        for n in start_nodes:
            _ = candidates.pop(n)
            
        while candidates:
            
            # Get contributions:
                ## Find candidates' contribution to the group
                ## Find members' contribution to not being in group
            node_contrib = numpy.zeros((n, 2))
            for i, c in enumerate(group_names):
                x = (test_groups == c).astype(int).reshape((1,n))
                node_contrib[:,i] = bMultiply(x.T, A, numpy.array(range(n)), L).reshape((n,))
            node_contrib = node_contrib.reshape((node_contrib.size,))