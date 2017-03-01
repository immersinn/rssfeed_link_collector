#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 17 14:03:56 2017

@author: immersinn
"""

import numpy
from scipy import sparse

import graph_utils
from graph_utils import modularity, bNG, bRandUni


def mKL(groups, A, indx, Bin='bNG', L=1.0,
        allow_make_new=False,
        verbose=False):
    """
    
    :type groups: numpy.array
    :param groups: 1D vector, size (n,); raw group assignments

    :type A: numpy.array, 2d; consider switching to scipy.sparse
    :param A: adjacency matrix
    
    :type indx: numpy.array
    :param indx: 1D vector, size (n,); 0/1 indicating whether node should be
                 included in analysis

    """
    
    # Prep work
    if Bin == 'bNG':
        B = lambda v, A, indx: bNG(v, A, indx, L)
    elif Bin == 'bRandUni':
        B = lambda v, A, indx: bRandUni(v, A, indx, L)
        
    
    n = A.shape[0]
    k = numpy.array(A.sum(axis=1))
    kk2m = ((k * k) / k.sum() * L).reshape((n,))

    groups = graph_utils.resetGroupNames(groups)
    score = modularity(groups, B, A)
    if verbose:
        print('Initial score: %s' % score)
    indx_orig = indx[:]
    score_prev = -999
    num_iter = 0
    
    # insert code for timing code

    while score > score_prev:
        score_prev = score
        num_iter += 1
        indx = indx_orig[:]
        group_names = numpy.unique(groups[indx])
        if verbose:
            print('At iteration %s: ' % num_iter)
            print('Group names: %s' % group_names)
        test_groups = groups.copy()
        
        indx = list(indx)
        
        while indx:
            
            node_contrib = numpy.zeros((n, len(group_names)))
            for i, c in enumerate(group_names):
                x = (test_groups == c).astype(int).reshape((1,n)) 
              # node_contrib[:,i] = bMultiply(x.T, A, numpy.array(range(n)), L).reshape((n,))
                node_contrib[:,i] = B(x.T, A, numpy.array(range(n))).reshape((n,))
                
            node_contrib = node_contrib.reshape((node_contrib.size,))            

            curr_contrib_index = (numpy.array(range(n)) * len(group_names)\
                                  + (test_groups - 1)).astype(int)
            curr_contrib = node_contrib[curr_contrib_index] + kk2m

            node_contrib = node_contrib -\
                           numpy.repeat(curr_contrib, len(group_names))
            node_contrib[curr_contrib_index] = -999
            node_contrib = node_contrib.reshape((n, len(group_names)))

            node_contrib = node_contrib[indx,]
            curr_contrib = curr_contrib[indx,]

            max_contrib = node_contrib.max()
            
            make_new = -curr_contrib.min() >= max_contrib

            if make_new and allow_make_new:
                best_node = indx[numpy.random.choice(\
                    numpy.where(curr_contrib == curr_contrib.min())[0])]
                best_group = test_groups.max() + 1
                group_names = numpy.resize(group_names,
                                           group_names.size + 1)
                group_names[-1] = best_group
            else:    
                (inds, grps) = numpy.where(node_contrib == max_contrib)
                rand_tie_break = numpy.random.randint(0, len(inds))
                best_node = indx[inds[rand_tie_break]]
                best_group = grps[rand_tie_break]


            test_groups[best_node] = best_group
            indx.remove(best_node)
            new_score = modularity(test_groups, B, A, indx_orig)
            
            if new_score > score:
                groups = test_groups.copy()
                score = new_score
                
        groups = graph_utils.resetGroupNames(groups)
        if verbose:
            print('New groups after iteration %s: %s' % (num_iter, groups))

    groups = graph_utils.reassignGroups(groups)
    return(groups, score)



def mKLLocal(core_nodes, A, indx, 
             start_nodes=[], 
             Bin='bNG', L=1.0,
             verbose=False):
    """
    Add nodes to a core group of nodes in a Kernighan–Lin manner
    """
    
    # Prep work
    if Bin == 'bNG':
        B = lambda v, A, indx: bNG(v, A, indx, L)
    elif Bin == 'bRandUni':
        B = lambda v, A, indx: bRandUni(v, A, indx, L)
    
    n = len(indx)
    k = numpy.array(A.sum(axis=1))[indx]
    kk2m = ((k * k) / k.sum() * L).reshape((n,))
    
    
    # Construct initial group
    group = numpy.zeros((n,))
    for i in core_nodes:
        group[i] = 1
    for i in start_nodes:
        group[i] = 1
    
    score = modularity(group, B, A, indx)
    if verbose:
        print('Initial score: %s' % score)
    indx_orig = indx[:]
    score_prev = -999
    num_iter = 0
    
    
    while score > score_prev:
        
        score_prev = score
        num_iter += 1
        indx = list(indx_orig[:])
        group_names = numpy.unique(group[indx])
        for k in core_nodes:
            indx.remove(k)  # remove core from consideration
    
        if verbose:
            print('At iteration %s: ' % num_iter)
        test_group = group.copy()
            
        while indx:
            
            # Get contributions:
                ## Find candidates' contribution to the group
                ## Find members' contribution to not being in group
            node_contrib = numpy.zeros((n, 2))
            for i, c in enumerate(group_names):
                x = (test_group == c).astype(int).reshape((1,n)) 
                node_contrib[:,i] = B(x.T, A, numpy.array(range(n))).reshape((n,))
            
            
            # THIS NEEDS TO BE MODIFIED DOWN THE ROAD
            node_contrib = node_contrib.reshape((node_contrib.size,))            
            
            curr_contrib_index = (numpy.array(range(n)) * len(group_names) + \
                                  test_group).astype(int)
            curr_contrib = node_contrib[curr_contrib_index] + kk2m

            node_contrib = node_contrib -\
                           numpy.repeat(curr_contrib, len(group_names))
            node_contrib[curr_contrib_index] = -999
            node_contrib = node_contrib.reshape((n, 2))
            
            node_contrib = node_contrib[indx,]
            curr_contrib = curr_contrib[indx,]
            
            max_contrib = node_contrib.max()
            
            
            # Get best move, rando break ties
            (inds, grps) = numpy.where(node_contrib == max_contrib)
            rand_tie_break = numpy.random.randint(0, len(inds))
            best_node = indx[inds[rand_tie_break]]
            best_group = grps[rand_tie_break]
            
            # Update node-group assignment
            test_group[best_node] = best_group
            indx.remove(best_node)
            new_score = modularity(test_group, B, A, indx_orig)
            
            if new_score > score:
                group = test_group.copy()
                score = new_score
                
        group = graph_utils.resetGroupNames(group)
#        if verbose:
#            print('New groups after iteration %s: %s' % (num_iter, group))

    group = graph_utils.reassignGroups(group)
    return(group, score)
            
            
            
def main():
    A = graph_utils.loadZachData()
    indx = numpy.array(range(A.shape[0]))
    groups = graph_utils.spanSpace(A.shape[0], 5)
    groups = mKL(groups, A, indx, Bin='bNG', L=1.0,
                 allow_make_new=True,
                 verbose=True)
    
if __name__=="__main__":
    main()