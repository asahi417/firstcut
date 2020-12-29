""" Non-negative Matric Factrization (NMF) """
from typing import List

import numpy as np
import librosa

EPS = np.spacing(1)


def euclid_divergence(y, yh):
    return 1 / 2 * (y ** 2 + yh ** 2 - 2 * y * yh).sum()


def kl_divergence(y, yh):
    return ((y * np.log(y / (yh + EPS))) - y + yh + EPS).sum()


def nmf(y,
        r: int = 20,
        n_iter: int = 50,
        div: str = "kl",
        basis_h: (List, np.array) = None,
        init_h: (List, np.array) = None,
        init_u: (List, np.array) = None):
    """ decompose non-negative matrix to components and activation with NMF

    y ≈　HU
    y ∈ r (m, n)
    h ∈ r (m, k)
    HU ∈ r (k, n)

     Parameter
    ----------------
    y: numpy.array
        target matrix to decompose
    r: int
        number of bases to decompose
    n_iter: int
        number for executing objective function to optimize
    div: str
        define divergence "kl" or "euc"
    init_h:
        initial value of h matrix. default value is random matrix
    init_u:
        initial value of u matrix. default value is random matrix

     Return
    ----------------
    Array of:
    0: matrix of h
    1: matrix of u
    2: array of cost transition
    """

    # size of input spectrogram
    assert np.ndim(y) == 2
    m, n = y.shape

    # initialization
    u = np.random.rand(r, n) if init_u is None else np.array(init_u)
    h = np.random.rand(m, r) if init_h is None else np.array(init_h)

    # reflect basis h
    if basis_h is None:
        fix_index = 0
    else:
        fix_index = np.array(basis_h).shape[1]
        assert fix_index < h.shape[1], "Over Size: {} > {}".format(fix_index, h.shape[1])
        h[0:, 0:fix_index] = basis_h

    # array to save the value of the euclid divergence
    cost = np.zeros(n_iter)

    # computation of lam (estimate of y)
    lam = np.dot(h, u)

    # iterative computation
    for i in range(n_iter):
        if div == "euc":
            # compute euclid divergence
            cost[i] = euclid_divergence(y, lam)
            # update h
            h *= np.dot(y, u.T) / (np.dot(np.dot(h, u), u.T) + EPS)
            if fix_index > 0:
                h[0:, 0:fix_index] = basis_h
            # update u
            u *= np.dot(h.T, y) / (np.dot(np.dot(h.T, h), u) + EPS)
        elif div == "kl":
            # compute euclid divergence
            cost[i] = kl_divergence(y, lam)
            # update h
            numerator_h = np.dot((y / (np.dot(h, u) + EPS)), u.T)
            denominator_h = np.tile(u.sum(axis=1), (m, 1))
            h *= numerator_h / (denominator_h + EPS)
            if fix_index > 0:
                h[0:, 0:fix_index] = basis_h
            # update u
            numerator_u = np.dot(h.T, (y / (np.dot(h, u) + EPS)))
            denominator_u = np.tile(h.sum(axis=0), (n, 1))
            u *= numerator_u / (denominator_u.T + EPS)
        else:
            raise ValueError('unknown divergence: {}'.format(div))
        # recomputation of lam
        lam = np.dot(h, u)
    return [h, u, cost]


def nmf_filter(y_o: List,
               y_n: List = None,
               basis_noise_num: int = 20,
               basis_num: int = 20):
    """ NMF based filter
    y_n: Noise Signal
    y_o: Original Signal
    """

    if y_n is None:
        y_n = y_o[:int(len(y_o) / 10)]

    # training
    y_n = librosa.stft(y_n)
    h_n, u_n, _ = nmf(np.abs(y_n), r=basis_noise_num)

    # separation
    y_o = librosa.stft(y_o)
    h_o, u_o, _ = nmf(np.abs(y_o), r=basis_noise_num + basis_num, basis_h=h_n)

    # wiener filter
    y_est = np.dot(h_o, u_o)
    y_target = np.dot(h_o[0:, basis_noise_num:basis_noise_num + basis_num],
                      u_o[basis_noise_num:basis_noise_num + basis_num, 0:])

    # smoothing
    y_mask = y_target / (y_est + EPS)

    y_sep = np.abs(y_o) ** 2 * y_mask
    y_phase = np.cos(np.angle(y_o) + 1j * np.sin(np.angle(y_o)))
    return librosa.istft(y_sep * y_phase)
