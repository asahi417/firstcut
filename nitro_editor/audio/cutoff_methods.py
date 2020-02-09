""" Collection of functions to tune cutoff amplitude """

import numpy as np
# from matplotlib import pyplot as plt
from ..util import create_log

VALID_METHOD_TYPES = ['percentile']
LOG = create_log()

__all__ = ['VALID_METHOD_TYPES', 'CutoffMethods']


class CutoffMethods:

    def __init__(self,
                 method_type='percentile'):
        if method_type not in VALID_METHOD_TYPES:
            raise ValueError('unknown `method_type`: %s not in %s' % (method_type, VALID_METHOD_TYPES))
        self.__method_type = method_type

    def get_cutoff_amp(self,
                       wave_data,
                       ratio: float=None):
        if self.__method_type in ['percentile']:
            if ratio is None:
                raise ValueError('method `percentile` requires `ratio`')
            return self.__percentile(wave_data, ratio)
        else:
            raise ValueError('unknown `method_type`: %s not in %s' % (self.__method_type, VALID_METHOD_TYPES))

    @staticmethod
    def __percentile(data, p):
        """ percentile method """
        p = np.clip(p, 0.0, 1.0)
        single_array_sorted = np.sort(np.abs(data))
        ind = int(np.floor(p * len(data)))
        val = single_array_sorted[min(ind, len(data) - 1)]
        LOG.debug('cutoff threshold (percentile method)')
        LOG.debug(' * percentile: %0.2f with %0.3f percentile' % (val, p))
        return int(val)

                # def visualize_cutoff_threshold(self,
    #                                wave_data,
    #                                frame_rate,
    #                                ratio: float = None,
    #                                path_to_save: str = None):
    #     th = self.get_cutoff_amp(wave_data, ratio=ratio)
    #
    #     fig = plt.figure(figsize=(6, 12))
    #     # plot wave and the cutoff threshold
    #     plt.subplot(2, 1, 1)
    #     plt.plot(wave_data)
    #     plt.plot([th] * len(wave_data), color='red', linestyle='--')
    #     plt.grid()
    #
    #     length_sec = int(len(wave_data) / frame_rate) + 1
    #     interval = min(10, length_sec)
    #     ind_1 = np.arange(0, length_sec + 1, int(length_sec / interval))
    #     ind_2 = ind_1 * frame_rate
    #     plt.title('Signal (sampling rate: %0.1f Hz)' % frame_rate)
    #     plt.xticks(ind_2, ind_1)
    #     plt.xlim([0, len(wave_data)])
    #     plt.xlabel("Time: total %0.2f sec." % (len(wave_data) / frame_rate))
    #     plt.ylabel("Amplitude")
    #
    #     # plot
    #     plt.subplot(2, 1, 2)
    #     plt.xticks(rotation=45)
    #     amp_sorted = np.sort(np.abs(wave_data))
    #     plt.plot(amp_sorted)
    #     plt.plot([th] * len(wave_data), color='red', linestyle='--')
    #     plt.grid()
    #     plt.title('Samples sorted by amplitude')
    #     plt.xlim([0, len(wave_data)])
    #     plt.xlabel("Cumulative sample size")
    #     plt.ylabel("Absolute amplitude")
    #
    #     if path_to_save is not None:
    #         plt.savefig(path_to_save, bbox_inches = 'tight')
