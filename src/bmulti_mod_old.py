#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 26 20:46:59 2017

@author: immersinn
"""



#def bMultiply(x, A, indx, L):
#    """
#    :type x: numpy.array
#    :param x: column vector, len n, 1 if node is in the current group,
#    0 otherwise
#
#    :type A: numpy.array, 2d; consider switching to scipy.sparse
#    :param A: adjacency matrix
#    """
#    j = numpy.array(A.sum(axis=1))  # column ndarray
#    jx = numpy.dot(j.T, x)  # scalar ndarray
#    m2 = j.sum()
#    x2 = A * x  # column ndarray
#    x3 = (L * jx / m2) * j  # column ndarray
#    v = x2 - x3  # column ndarray
#    v = v[indx]
#    return(v) 


#def modularity(g, A, L):
#    """
#    Newman modularity.
#
#    :type A: numpy.array, 2d
#    :param graph: adjacency matrix
#
#    :type groups: numpy.array
#    :param groups: array of length n, where n = graph.number_of_nodes().
#    Indicates which nodes belong to which groups, where each node is assigned
#    an integer corresponding to the group index
#
#    :type L: float (or int, but force float)
#    :param L: lambda
#
#   """
#    
#    #
#    n = A.shape[0]
#    
#    # Nodes of interest
#    indx = numpy.array(range(A.shape[0]))
#    
#    # Current communities / groups
#    comms = numpy.unique(g)
#
#    # Calculate current Q
#    Q = 0.
#    for c in comms:
#        x = (g==c).reshape((1,n))  # row ndarray
#        Q += numpy.dot(x, bMultiply(x.T, A, indx, L))
#    Q = Q / A.sum()
#    Q = Q[0][0]
#    
#    return(Q)
    