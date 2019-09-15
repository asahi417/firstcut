""" Collection of functions to tune cutoff amplitude """

import numpy as np
from ..util import create_log

VALID_METHOD_TYPES = ['percentile']
LOG = create_log()


class CutoffMethods:

    def __init__(self, method_type='percentile'):
        if method_type not in VALID_METHOD_TYPES:
            raise ValueError('unknown `method_type`: %s not in %s' % (method_type, VALID_METHOD_TYPES))
        self.__method_type = method_type

    def get_cutoff_amp(self, wave_data, ratio: float=None):
        if self.__method_type in ['percentile']:
            if ratio is None:
                raise ValueError('`percentile` requires `ratio` parameter')
            return self.__percentile(wave_data, ratio)

    @staticmethod
    def __percentile(data, p):
        """ percentile """
        p = np.clip(p, 0.0, 1.0)
        single_array_sorted = np.sort(np.abs(data))
        ind = int(np.floor(p * len(data)))
        val = single_array_sorted[min(ind, len(data) - 1)]
        LOG.debug('cutoff threshold (percentile method)')
        LOG.debug(' * percentile: %0.2f with %0.3f percentile' % (val, p))
        return int(val)
