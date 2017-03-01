#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 20 16:03:23 2017

@author: immersinn
"""

"""
cd /Users/immersinn/Google\ Drive/Analytics/wiki_analytics/comparitive_clustering/python_code/
python testKlnLoop.py
"""

import numpy
from scipy.sparse.linalg import eigsh
from scipy.sparse.linalg import LinearOperator
from scipy.sparse.linalg.eigen.arpack.arpack import ArpackNoConvergence

import graph_utils
from graph_utils import modularity, bNG, bRandUni
from kernighan_lin import mKL


PASSQ3FACTOR = 1
pi = numpy.pi

"""
How to build the LinearOperator object to feed into eigs(h) function:

B = lambda v, A, indx: bNG(v, A, indx, 1.0)
BtoEigs = LinearOperator((8,8),
                         matvec = lambda x: B(x, A, indx))
vals, vecs = eigs(BtoEigs, k = 3, which='LM')
"""





def spectralGraphPartition23(A, Bin='bNG', L=1.0, finetune=False, n_cutoff=4):
    """

    """
    # Prep work
    if Bin == 'bNG':
        B = lambda v, A, indx: bNG(v, A, indx, L)
    elif Bin == 'bRandUni':
        B = lambda v, A, indx: bRandUni(v, A, indx, L)
    else:
        err_msg = 'Invalid specification for B function; "bNG" or "bRandUni" only.'
        raise ValueError(err_msg)
    A = preprocessA(A)

    # Find best groups
    groups, counts, history = mainRecursivePartitioningLoop(A, B, n_cutoff)
#    if finetune:
#        groups = mKL(groups, A, range(A.shape[0]), L,
#                     allow_make_new=True)

    groups = graph_utils.reassignGroups(groups)

    return(groups, counts, history)


def spectralGraphPartitionSingle(A, Bin='bNG', L=1.0, 
                                 method='twoway1', n_sections=24):
    """
    Single-pass of spectral method using the selected method
    
    """
    
    
    # Prep work
    if Bin == 'bNG':
        B = lambda v, A, indx: bNG(v, A, indx, L)
    elif Bin == 'bRandUni':
        B = lambda v, A, indx: bRandUni(v, A, indx, L)
    else:
        err_msg = 'Invalid specification for B function; "bNG" or "bRandUni" only.'
        raise ValueError(err_msg)
    A = preprocessA(A)
    ni = A.shape[0]
    indx = [i for i  in range(ni)]
    
    
    # Define method lambda function
    if method=='twoway1':
        f = lambda vvv:  twoway1(vvv, B, A, indx)
    elif method=='twoway2':
        f = lambda vvv:  twoway2(vvv, B, A, indx)
    elif method=='threeway2':
        f = lambda vvv:  threeway2(vvv, B, A, indx)
    elif method=='threewayCoarse':
        f = lambda vvv:  threewayCoarse(vvv, B, A, indx, n_sections)
    
    # Calc and sort eigenvecs, eigenvalues
    BtoEigs = LinearOperator((ni, ni),
                             matvec = lambda x: B(x, A, indx),
                             dtype = numpy.float64)
    
    try:
        if method in ['twoway2', 'threeway2']:
            vals, vecs = eigsh(BtoEigs, k=3, which='BE')
            sort_inds = numpy.argsort(-vals)
            vals = vals[sort_inds]
            vecs = vecs[:,sort_inds]
        elif method in ['twoway1']:
            vals, vecs = eigsh(BtoEigs, k=2, which='LA')
            sort_inds = numpy.argsort(-vals)
            vals = vals[sort_inds]
            vecs = vecs[:,sort_inds]
            vals = numpy.array([vals[0], vals[1], min(0, vals[1] - 1)])
    except ArpackNoConvergence:
        vecs, vals = numpy.array(), numpy.array()
        
    
    # Find clusters 
    C = f(vecs)
    M = modularity(C, B, A, indx)
    
    return(C, M)


def preprocessA(A):
    """
    """
    A = A - numpy.diag(A.diagonal())
    return(A)
    


def mainRecursivePartitioningLoop(A, B, n_cutoff):
    """

    """
    # Initialize storage objects
    n = A.shape[0]
    groups = numpy.zeros((n,), dtype=int)
    groups_history = []
    counts = {'twoway-single' : 0,
              'twoway-pair' : 0,
              'threeway-pair' : 0}
    to_split = {0 : True}

    # Recursively partition network
    while numpy.any([v for v in to_split.values()]):

        for gn in [g for g,v in to_split.items() if v]:
            
            # Initialize group info
            indx = numpy.where(groups==gn)[0]
            ni = len(indx)
            #c = numpy.zeros((1,3))
            
            if ni > n_cutoff:

                # Calc and sort eigenvecs, eigenvalues
                BtoEigs = LinearOperator((ni, ni),
                                         matvec = lambda x: B(x, A, indx),
                                         dtype=float)
                try:
                    if ni > 2:
                        vals, vecs = eigsh(BtoEigs, k=3, which='BE')
                        sort_inds = numpy.argsort(-vals)
                        vals = vals[sort_inds]
                        vecs = vecs[:,sort_inds]
                    else:
                        vals, vecs = eigsh(BtoEigs, k=2, which='LA')
                        sort_inds = numpy.argsort(-vals)
                        vals = vals[sort_inds]
                        vecs = vecs[:,sort_inds]
                        vals = numpy.array([vals[0], vals[1], min(0, vals[1] - 1)])
                except ArpackNoConvergence:
                    to_split[gn] = False
                            
                
                # Initialize temporary score and groups holders
                temp_Q = {}
                temp_C = {}
    
                # Leading eignevec 2-way
                temp_C['twoway-single'] = twoway1(vecs, B, A, indx)
                temp_Q['twoway-single'] = modularity(temp_C['twoway-single'],
                                                     B, A, indx)
    
                # Convert eigenvecs to vertex vectors
                mod_factor = numpy.sqrt(vals[:2] - vals[2])
                vecs = vecs[:,0:2] * mod_factor
    
                # Leading two eigenvec 2-way
                temp_C['twoway-pair'] = twoway2(vecs, B, A, indx)
                temp_Q['twoway-pair'] = modularity(temp_C['twoway-pair'],
                                                   B, A, indx)
    
#                # Leading two eigenvec 3-way
#                temp_C['threeway-pair'] = threewayCoarse(vecs, B, A, indx, 24)
#                temp_Q['threeway-pair'] = modularity(temp_C['threeway-pair'],
#                                                     B, A, indx)
#    
                # Determine best Score, Grouping
                best_split_ind = [k for k in temp_Q.keys()]\
                                 [numpy.where(list(temp_Q.values())==max(temp_Q.values()))[0][0]]
                best_Q = temp_Q[best_split_ind]
                best_C = temp_C[best_split_ind]
    
                # Update master group store, info regarding availalbe splitting
                if (best_Q > 0) and (max(best_C) - min(best_C) > 0):
                    counts[best_split_ind] += 1
                    g0 = numpy.array(best_C)==0
                    g1 = numpy.array(best_C)==1
                    g2 = numpy.array(best_C)==2
                    max_gn = max(groups)
                    groups[indx[g1]] = max_gn + 1
                    groups[indx[g2]] = max_gn + 2
                    to_split[gn] = sum(g0) > 2
                    to_split[max_gn + 1] = sum(g1) > 2
                    to_split[max_gn + 2] = sum(g2) > 2
                    groups_history.append(groups.copy())
                else:
                    to_split[gn] = False
                            
            else:
                to_split[gn] = False
                        
    groups_history = numpy.array(groups_history).T
                        
                
    return(groups, counts, groups_history)
            


def cart2pol(x, y):
    rho = numpy.sqrt(x**2 + y**2)
    phi = numpy.arctan2(y, x)
    return(phi, rho)


def pol2cart(rho, phi):
    x = rho * numpy.cos(phi)
    y = rho * numpy.sin(phi)
    return(x, y)


def twoway1(vecs, B, A, indx):
    C = vecs[:,0]
    C[C>=0] = 0
    C[C<0] = 1
    C = C.astype(int).reshape((len(indx),))
    return(C)


def twoway2(vecs, B, A, indx):
    """
    [pthetas,rdummy]=cart2pol(V(:,1),V(:,2));
    temp=sort(mod(pthetas,pi));
    cutthetas=temp-min(diff([0;temp]))/2;
    ng=length(indx);
    QQ=zeros(1,ng);
    for icut=1:ng, %overkill, could be improved
        C=ones(ng,1);
        relangle=mod(pthetas-cutthetas(icut)+pi,2*pi)-pi;
        C(relangle<0)=2;
        QQ(icut)=modularity(C',B,A,indx); %overkill, could be improved
    end
    [Q2,maxcut]=max(QQ);
    C2=ones(1,ng);
    relangle=mod(pthetas-cutthetas(maxcut)+pi,2*pi)-pi;
    C2(relangle<0)=2;
    pass=C2;
    """

    theta, rho = cart2pol(vecs[:,0], vecs[:,1])
    temp = numpy.sort(theta % pi)
    all_locations = [0]
    all_locations.extend(temp.tolist())
    cut_thetas = temp - numpy.diff(all_locations).min()
    
    ni = len(indx)
    QQ = []
    for cut_ind in range(ni):
        C = numpy.zeros((ni,), dtype=int)
        relangle = (theta - cut_thetas[cut_ind] + pi) % (2 * pi) - pi
        C[relangle < 0] = 1
        QQ.append(modularity(C.tolist(), B, A, indx))

    best_cut_ind = numpy.argmax(QQ)
    best_groups = numpy.zeros((ni,), dtype=int)
    relangle = (theta - cut_thetas[best_cut_ind] + pi) % (2 * pi) - pi
    best_groups[relangle < 0] = 1
    return best_groups.tolist()


def threeway2(vecs, B, A, indx):
    """
    global PASSQ3FACTOR
    disp(['threeway2: length(indx)=',int2str(length(indx))])
    maxwedges=min(2^15,length(indx));
    Q0=-999;
    numcoarsewedges=4;
    [Q,C]=threewaycoarse(V,B,A,indx,numcoarsewedges);
    QQ=Q;
    while (Q>Q0+(PASSQ3FACTOR-1)*abs(Q0))&&(numcoarsewedges*2<=maxwedges)
        Q0=Q;
        numcoarsewedges=numcoarsewedges*2;
        [Q,C]=threewaycoarse(V,B,A,indx,numcoarsewedges);
        QQ=[QQ,Q];
        disp(num2str(QQ))
    end
    %disp(['threeway2: ',num2str(QQ)])
    pass=C;
    """

    max_wedges = min(2**15, len(indx))
    Q0 = -999
    num_coarse_wedges = 4
    Q, C = threewayCoarse(vecs, B, A, indx, num_coarse_wedges)
    QQ = [Q]

    while (Q > Q0 + (PASSQ3FACTOR - 1) * abs(Q0)) and\
          num_coarse_wedges * 2 < max_wedges:
        Q0 = Q
        num_coarse_wedges *= 2
        Q, C = threewayCoarse(vecs, B, A, indx, num_coarse_wedges)
        QQ.append(Q)

    return C
    


def threewayCoarse(vecs, B, A, indx, num_coarse_wedges, return_mod=False):
    """

    """
    
    theta, rho = cart2pol(vecs[:,0], vecs[:,1])
    ni = len(indx)

    if ni > 8:
        cut_thetas = numpy.array([-1, 0, 1, 2]) * pi * 0.5
        if num_coarse_wedges > 4:
            vecs_stds = numpy.std(vecs, axis=0)
            corner_angle, _ = cart2pol(vecs_stds[0], vecs_stds[1])
            numper8 = num_coarse_wedges / 8
            quadrant = numpy.array([numpy.linspace(0, corner_angle, numper8 + 1),
                                    numpy.linspace(corner_angle, pi / 2, numper8 + 1)])
            quadrant = quadrant.reshape((1, quadrant.size))
            angles = numpy.array([quadrant, pi - quadrant,
                                  -quadrant, -pi + quadrant]).\
                                  reshape((1, 4 * quadrant.size))
            angles = numpy.sort(numpy.unique(angles))
            cut_thetas = angles[1:]
    else:
        cut_thetas = numpy.sort(theta)

    n_cuts = cut_thetas.size
    Q3 = -999
    C3 = numpy.zeros((1, ni))
    #total_iters = ni * (ni - 1) * (ni - 2) / 6
    QQ = []
    count = 0

    for i1 in range(n_cuts - 2):                # down
        for i2 in range((i1 + 1), (n_cuts - 1)):# the
            for i3 in range((i2 + 1), n_cuts):  # tiny rabbit hole...
                C = numpy.zeros((ni, ), dtype=int)
                C[(theta > cut_thetas[i1]) * (theta <= cut_thetas[i2])] = 1
                C[(theta > cut_thetas[i2]) * (theta <= cut_thetas[i3])] = 2
                Q = modularity(C.tolist(), B, A, indx)
                QQ.append(Q)
                count += 1
                if Q > Q3:
                    C3 = C
                    Q3 = Q
                    
    count -= 1
    C3 = C3.tolist()

    if return_mod:
        return(Q3, C3)
    else:
        return(C3)





def main():
    """
    BPASSGENFLAG=1;

    %Establish B(v) function returning B(g)*v for arbitrary v vector
    if exist('Bin','var')==0
        B = @(v,A,IX) BNG(v,A,IX,1); %if Bin is not specified
    elseif isempty(Bin)
        B = @(v,A,IX) BNG(v,A,IX,1); %if Bin is not specified
    elseif ishandle(Bin)
        B = Bin;
    elseif max(size(Bin))==1
        if Bin>0
            B = @(v,A,IX) BNG(v,A,IX,Bin); %if Bin is a positive scaler
        else
            B = @(v,A,IX) Buniform(v,A,IX,-Bin); %if Bin is a negative scaler
        end
    else
        disp('Problem determing how to work with B')
        return
    end

    if exist('klnflag','var')==0
        klnflag=1; %do KLN postprocessing by default
    end

    if exist('extsubflag','var')==0
        extsubflag=1; %do extended subdivision by default
    end

    if exist('flag3','var')==0
        flag3=1; %include three-way divisions by default
    end

    if exist('Q3factor','var')==0
        Q3factor=1; %Continue 3-way divide-and-conquer on any improvement
    end
    PASSQ3FACTOR=Q3factor;
    
    """
   
##    A = loadRandom()
##    A = loadBucketBrigade()
    A = graph_utils.loadZachData()
    groups = spectralGraphPartition23(A, Bin='bNG', finetune=False)
    B = lambda v, A, indx: bNG(v, A, indx, 1.0)
    score = modularity(groups, B, A, range(A.shape[0]))
    print("Final groups: %s" % groups)
    print("Final score: %s" % score)


if __name__ == "__main__":
    main()

