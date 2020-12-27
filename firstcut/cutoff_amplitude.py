""" Collection of functions to tune cutoff amplitude """
import numpy as np
from matplotlib import pyplot as plt


__all__ = ('get_cutoff_amplitude', 'visualize_cutoff_amplitude')


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


def visualize_cutoff_amplitude(cutoff_amplitude: int,
                               wave_data,
                               frame_rate: float = None,
                               path_to_save: str = './visualize_cutoff_amplitude.png'):
    """ Visualize cutoff amplitude

     Parameter
    -----------
    cutoff_amplitude: cutoff amplitude attained from `get_cutoff_amplitude`
    wave_data: 1d nd.array
        mono wave signal
    frame_rate: float
    path_to_save: str
    """

    frame_rate = len(wave_data) if frame_rate is None else frame_rate
    fig = plt.figure(figsize=(6, 12))
    # plot wave and the cutoff threshold
    plt.subplot(2, 1, 1)
    plt.plot(wave_data)
    plt.plot([cutoff_amplitude] * len(wave_data), color='red', linestyle='--')
    plt.grid()

    length_sec = int(len(wave_data) / frame_rate) + 1
    interval = min(10, length_sec)
    ind_1 = np.arange(0, length_sec + 1, int(length_sec / interval))
    ind_2 = ind_1 * frame_rate
    plt.title('Signal (sampling rate: {} Hz)'.format(round(frame_rate, 2)))
    plt.xticks(ind_2, ind_1)
    plt.xlim([0, len(wave_data)])
    plt.xlabel("Time: total {} sec.".format(round(len(wave_data) / frame_rate), 2))
    plt.ylabel("Amplitude")

    # plot
    plt.subplot(2, 1, 2)
    plt.xticks(rotation=45)
    amp_sorted = np.sort(np.abs(wave_data))
    plt.plot(amp_sorted)
    plt.plot([cutoff_amplitude] * len(wave_data), color='red', linestyle='--')
    plt.grid()
    plt.title('Samples sorted by amplitude')
    plt.xlim([0, len(wave_data)])
    plt.xlabel("Samples")
    plt.ylabel("Absolute amplitude")

    plt.savefig(path_to_save, bbox_inches='tight')
