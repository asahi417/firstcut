""" Collection of functions to tune cutoff amplitude """
import numpy as np

__all__ = 'get_cutoff_amplitude'


def get_cutoff_amplitude(wave_data, cutoff_ratio: float = 0.5, method_type: str = 'ratio'):
    """ Get cutoff amplitude

     Parameter
    -----------
    wave_data: 1d nd.array
        mono wave signal
    cutoff_ratio: float
        cutoff percentile (higher removes more sample)

     Return
    -----------
    cutoff amplitude: float
    """
    assert np.ndim(wave_data) == 1
    if method_type == 'ratio':
        cutoff_ratio = np.clip(cutoff_ratio, 0.0, 1.0)
        single_array_sorted = np.sort(np.abs(wave_data))
        ind = int(np.floor(cutoff_ratio * len(wave_data)))
        val = single_array_sorted[min(ind, len(wave_data) - 1)]
        return int(val)
    else:
        raise ValueError('unknown `method_type`: {}'.format(method_type))
