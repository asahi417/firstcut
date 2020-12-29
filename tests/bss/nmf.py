import numpy as np
def NMF(Y, R=20, n_iter=50, div="KL", basis_H=[], init_H=[], init_U=[] ):
    """
    decompose non-negative matrix to components and activation with NMF
    
    Y ≈　HU
    Y ∈ R (m, n)
    H ∈ R (m, k)
    HU ∈ R (k, n)
    
    parameters
    ---- 
    Y: target matrix to decompose
    R: number of bases to decompose
    n_iter: number for executing objective function to optimize
    div: define divergence "KL" or "EUC" 
    init_H: initial value of H matrix. default value is random matrix
    init_U: initial value of U matrix. default value is random matrix

    return
    ----
    Array of:
    0: matrix of H
    1: matrix of U
    2: array of cost transition
    """
    eps = np.spacing(1)
    
    # size of input spectrogram
    M = Y.shape[0]
    N = Y.shape[1]
    
    # initialization
    if len(init_U):
        U = init_U
        R = init_U.shape[0]
    else:
        U = np.random.rand(R,N)

    if len(init_H):
        H = init_H
        R = init_H.shape[1]
    else:
        H = np.random.rand(M,R)

    # reflect basis H
    fixIndex = 0
    if len(basis_H):
        fixIndex = basis_H.shape[1]
        if fixIndex > H.shape[1]: 
            assert False, "Over Size"
        else:
            H[0:,0:fixIndex] = basis_H

    # array to save the value of the euclid divergence
    cost = np.zeros(n_iter)

    # computation of Lambda (estimate of Y)
    Lambda = np.dot(H, U)

    # iterative computation
    for i in range(n_iter):
        if div == "EUC":
            # compute euclid divergence
            cost[i] = euclid_divergence(Y, Lambda)
            # update H
            H *= np.dot(Y, U.T) / (np.dot(np.dot(H, U), U.T) + eps)
            if fixIndex > 0:
                H[0:,0:fixIndex] = basis_H
            # update U
            U *= np.dot(H.T, Y) / (np.dot(np.dot(H.T, H), U) + eps)
            # recomputation of Lambda
            Lambda = np.dot(H, U)
        elif div == "KL":
            # compute euclid divergence
            cost[i] = kl_divergence(Y, Lambda)
            # update H
            numeratorH = np.dot(( Y / (np.dot(H, U) + eps) ), U.T)
            denominatorH = np.tile(U.sum(axis=1), (M ,1))
            H *= numeratorH / (denominatorH + eps)
            if fixIndex > 0:
                H[0:,0:fixIndex] = basis_H
            # update U
            numeratorU = np.dot(H.T, ( Y / (np.dot(H, U) + eps) ))
            denominatorU = np.tile(H.sum(axis=0), (N ,1))
            U *= numeratorU / (denominatorU.T + eps)
            # recomputation of Lambda
            Lambda = np.dot(H, U)
    return [H, U, cost]

def euclid_divergence(Y, Yh):
    d = 1 / 2 * (Y ** 2 + Yh ** 2 - 2 * Y * Yh).sum()
    return d

def kl_divergence(Y, Yh):
    eps = np.spacing(1)
    Yh = Yh + eps
    d = ( (Y * np.log(Y/Yh)) - Y + Yh ).sum()
    return d
