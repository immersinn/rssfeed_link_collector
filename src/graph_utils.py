#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 26 20:13:32 2017

@author: immersinn
"""


import numpy
from scipy import sparse


BPASSFLAG = 1


def modularity(groups, B, A, indx=numpy.array(())):
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
    
    :type indx: numpy.array
    :param indx: indicates which nodes are to be considered for the mod calc
    
    
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
    
    if len(indx) == 0:
        indx = numpy.array(range(A.shape[0]))

    Q = 0
    for i in numpy.unique(groups):
        x = numpy.array((groups==i).astype(int)).reshape((1,len(indx)))
        Q = Q + numpy.dot(x, B(x.T, A, indx))
    return Q[0,0]


def calcB(A):
    """
    DO NOT USE EXCEPT FOR SMALL NETWORKS, ERROR CHECKING!!!!!
    
    B_ij = A_ij - P_ij
    P_ij = k_i * k_j / 2m
    """
    n = A.shape[0]
    j = A.sum(axis=1)
    two_m = A.sum()
    P = numpy.dot(j.reshape((n,1)), j.reshape((1,n))) / two_m
    B = A - P
    return B


def bNG(v, A, indx, L):
    """
    Pre-multiplication of general column vector v by the Newman-Girvan
    generalized modularity matrix on indices IX

    x: row vector; len(x) = len(indx)

    A: adj matrix

    indx: indicies of nodes of interest

    L: lambda
    """
    n = A.shape[0]
    ni = len(indx)
    v = v.reshape((ni,1))
    j = A.sum(axis=1).reshape((1, n))
    sub_A = A[numpy.ix_(indx, indx)]
    sub_j = sub_A.sum(axis=1).reshape((ni, 1))
    ind_j = j[0, indx].reshape((1, ni))
    
    x1 = numpy.multiply(v, sub_j)
    x2 = numpy.multiply(v, ind_j.T) * L * ind_j.sum() / j.sum()
    vBsum = x1 - x2
    x3 = sub_A.dot(v)
    x4 = L * ind_j.T * numpy.dot(sub_j.T, v) / j.sum()
    x5 = x3 - x4
    return x5 - BPASSFLAG * vBsum
    


def bRandUni(v, A, indx, L):
    """
    Pre-multiplication of general column vector v by the random uniform
    generalized modularity matrix on indices IX

    x: row vector; len(x) = len(indx)

    A: adj matrix

    indx: indicies of nodes of interest

    L: lambda


    """
    #n = A.shape[0]
    ni = len(indx)
    v = v.reshape((ni,1))
    #j = A.sum(axis=1).reshape((1, n))
    sub_A = A[numpy.ix_(indx, indx)]
    sub_j = sub_A.sum(axis=1).reshape((ni, 1))
    #ind_j = j[0, indx].reshape((1, ni))

    x1 = numpy.multiply(v, sub_j)
    x2 = v * L * len(indx)
    vBsum = x1 - x2
    x3 = sub_A.dot(v)
    x4 = L * v
    x5 = x3 - x4
    return x5 - BPASSFLAG * vBsum


def resetGroupNames(groups):
    """Reassigns groups so that start at '0' and no gaps
    """
    group_names = numpy.unique(groups)
    new_group_names = numpy.array(range(len(group_names)))
    group_lookup = {k:v for (k,v) in zip(group_names, new_group_names)}
    groups = numpy.array([group_lookup[g] for g in groups])
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


def loadZachData():
    """
    key = numpy.array([0,0,0,0,0,0,0,0,1,1,0,0,0,0,1,1,0,0,1,0,1,0,1,1,1,1,1,1,1,1,1,1,1,1])
    """
    A = get_kc_graph()
    return(A)


def get_kc_string():
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
    return(karate_club_raw)


def loadZachEdgelist():
    
    edges = []
    
    krs = get_kc_string()
    krs = ' '.join(krs.split('\n')).strip()
    entries = krs.split('] [')
    
    if len(entries)==1:
        i,j = entries[0][1:-1].split()
        edges.append((int(i),int(j)))
    else:
        # 1st entry
        i,j = entries[0][1:].split()
        edges.append((int(i),int(j)))
    
        # Middle entries
        for entry in entries[1:-1]:
            i,j = entry.split()
            edges.append((int(i),int(j)))
    
        # Last entry
        i,j = entries[-1][:-1].split()
        edges.append((int(i),int(j)))
        
    return(edges)


def get_kc_graph():
    """
    
    """
    
    karate_club_raw = get_kc_string()

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
            ii.append(int(j))
            jj.append(int(i))
    
        # Last entry
        i,j = entries[-1][:-1].split()
        ii.append(int(i))
        jj.append(int(j))
                
    data = [1 for _ in range(len(ii))]
    ii = [i - 1 for i in ii]
    jj = [j - 1 for j in jj]
    
    A = sparse.coo_matrix((data, (ii,jj)), shape=(34,34))
    A = A.tocsr()
    return(A)


def loadBucketBrigade():
    """
    key = numpy.array([1,1,2,2,3,3,4,4])
    """
    A = numpy.array([[0,1,0,0,0,0,0,0],
                     [1,0,1,0,0,0,0,0],
                     [0,1,0,1,0,0,0,0],
                     [0,0,1,0,1,0,0,0],
                     [0,0,0,1,0,1,0,0],
                     [0,0,0,0,1,0,1,0],
                     [0,0,0,0,0,1,0,1],
                     [0,0,0,0,0,0,1,0]])
    return(A)


def loadRandom(n=30, cutoff=0.2):
    A = (numpy.random.uniform(size=n*n) < cutoff).\
        astype(int).\
        reshape((n, n))
    A = A + A.T
    A[A==2] = 1
    A = A - numpy.diag(A.diagonal())
    return A


def spanSpace(n, max_groups):
    """
    Randomly assigns nodes to a random number of groups (less than
    or equal to 'max_groups')

    :type n: int
    :param n: number of nodes in the graph

    :type max_groups: numeric
    :param max groups: indicates the maximum number of groups the nodes
    are to be split into
    """
    
    groups_index = numpy.random.randint(1,
                                        high=numpy.random.randint(2, max_groups + 1) + 1,
                                        size=n)
    groups_index = groups_index.reshape((n,))
    return(groups_index)
    