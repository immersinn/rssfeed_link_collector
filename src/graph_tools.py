#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 17 14:03:56 2017

@author: immersinn
"""

import numpy
import scipy
from scipy import sparse


karate_club_raw = """
[2 1]
[3 1] [3 2]
[4 1] [4 2] [4 3]
[5 1]
[6 1]
[7 1] [7 5] [7 6]
[8 1] [8 2] [8 3] [8 4]
[9 1] [9 3]
[10 3]
[11 1] [11 5] [11 6]
[12 1]
[13 1] [13 4]
[14 1] [14 2] [14 3] [14 4]
[17 6] [17 7]
[18 1] [18 2]
[20 1] [20 2]
[22 1] [22 2]
[26 24] [26 25]
[28 3] [28 24] [28 25]
[29 3]
[30 24] [30 27]
[31 2] [31 9]
[32 1] [32 25] [32 26] [32 29]
[33 3] [33 9] [33 15] [33 16] [33 19] [33 21] [33 23] [33 24] [33 30] [33 31] [33 32]
[34 9] [34 10] [34 14] [34 15] [34 16] [34 19] [34 20] [34 21] [34 23] [34 24] [34 27] [34 28] [34 29] [34 30] [34 31] [34 32] [34 33]
"""


def get_kc_graph():
    """
    
    """
    ii = []
    jj = []
    karate_club_raw = ' '.join(karate_club_raw.split('\n')).strip()
    entries = karate_club_raw.split('] [')
    if len(entries)==1:
        i,j = entries[0][1:-1].split()
        ii.append(int(i))
        jj.append(int(j))
    else:
        # 1st entry
        i,j = entries[0][1:].split()
        ii.append(int(i))
        jj.append(int(j))
    
        # Middle entries
        for entry in entries[1:-1]:
            i,j = entry.split()
            ii.append(int(i))
            jj.append(int(j))
    
        # Last entry
        i,j = entries[-1][:-1].split()
        ii.append(int(i))
        jj.append(int(j))
                
    data = [1 for _ in range(len(ii))]
    ii = [i - 1 for i in ii]
    jj = [j - 1 for j in jj]
    
    A = sparse.coo_matrix((data, (ii,jj)), shape=(34,34))
    
    return(A)


def bMultiply(x, A, indx, L):
    """
    :type x: numpy.array
    :param x: column vector, len n, 1 if node is in the current group,
    0 otherwise

    :type A: numpy.array, 2d; consider switching to scipy.sparse
    :param A: adjacency matrix
    """
    j = numpy.array(A.sum(axis=1))  # column ndarray
    jx = numpy.dot(j.T, x)  # scalar ndarray
    m2 = j.sum()
    x2 = A * x  # column ndarray
    x3 = (L * jx / m2) * j  # column ndarray
    v = x2 - x3  # column ndarray
    v = v[indx]
    return(v) 


def modularity(g, A, L):
    """
    Newman modularity.

    :type A: numpy.array, 2d
    :param graph: adjacency matrix

    :type groups: numpy.array
    :param groups: array of length n, where n = graph.number_of_nodes().
    Indicates which nodes belong to which groups, where each node is assigned
    an integer corresponding to the group index

    :type L: float (or int, but force float)
    :param L: lambda

    From Newman:
        
        Q = (1/2m) * sum_(i,j) [A_(i,j) - P_(i,j)]delta(g_i, g_j)
        
        + A is adj mat
        + P is the "null model" matrix
        
    Other:
        
        Q(A,C) = (1/2|E|) * sum_over_edges { ( a_(i,i') - (a_(i,.) * a(i', .)) / (2|E|) ) * c_(i,i')}
        
        + A is the adj matrix
        + C is the cluster assignment
        + E is the edge list
        + a_(i, i') is the binary edge indicator for the pair of nodes i, i' (symmetric adj matrix)
        + c_(i,i') is the indicatory function for nodes i, i' being assigned to the same cluster
    """
    
    #
    n = A.shape[0]
    
    # Nodes of interest
    indx = numpy.array(range(A.shape[0]))
    
    # Current communities / groups
    comms = numpy.unique(g)

    # Calculate current Q
    Q = 0.
    for c in comms:
        x = (g==c).reshape((1,n))  # row ndarray
        Q += numpy.dot(x, bMultiply(x.T, A, indx, L))
    Q = Q / A.sum()
    Q = Q[0][0]
    
    return(Q)
    


def mKL(groups, A, indx, L,
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
    
    n = A.shape[0]
    k = numpy.array(A.sum(axis=1))
    kk2m = ((k * k) / k.sum() * L).reshape((n,))

    groups = resetGroupNames(groups)
    score = modularity(groups, A, L)
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
        
        while indx:
            
            node_contrib = numpy.zeros((n, len(group_names)))
            for i, c in enumerate(group_names):
                x = (test_groups == c).astype(int).reshape((1,n))
                node_contrib[:,i] = bMultiply(x.T, A, numpy.array(range(n)), L).reshape((n,))
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
            new_score = modularity(test_groups, A, L)
            if new_score > score:
                groups = test_groups.copy()
                score = new_score
                
        groups = resetGroupNames(groups)
        if verbose:
            print('New groups after iteration %s: %s' % (num_iter, groups))

    groups = reassignGroups(groups)
    return groups, score


def resetGroupNames(groups):
    """Reassigns groups so that start at '0' and no gaps
    """
    s = groups.shape
    group_names = list(numpy.unique(groups))
    group_lookup = {old : new for new,old in enumerate(group_names)}
    groups = numpy.array([group_lookup[g] for g in groups]).reshape(s)
    return groups


def reassignGroups(groups):
    """
    Renumbers groups so numbers start at '0' and no gaps and
    1st node in group 1, group 2 starts with 1st node not in same
    group as node 1, etc.
    """
    group_names = numpy.unique(groups)
    num_groups = len(group_names)
    groups += group_names[-1]
    group_names += group_names[-1]

    pos_index = numpy.ones((num_groups,), dtype=int) * -1
    for i, g in enumerate(group_names):
        pos_index[i] = numpy.where(groups==g)[0][0]
    pos_index.sort()
    for i in range(num_groups):
        groups[numpy.where(groups==groups[pos_index[i]])] = i
    return groups



"""
EXAMPLE:
    
groups_mkl, score = graph_tools.mKL(groups, 
                                spectral_partition.preprocessA(tsg_cci),
                                [i for i in range(tsg_cci.shape[0])],
                                1.0,
                                allow_make_new=True,
                                verbose=True)

"""