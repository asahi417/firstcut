import numpy as np
# import seaborn as sns
from matplotlib import pyplot as plt
"""
TODO: prettify the graphs
"""
# sns.set_style("darkgrid")

__all__ = ('visualize_cutoff_amplitude', 'visualize_noise_reduction')


def visualize_cutoff_amplitude(wave_data,
                               cutoff_ratio,
                               cutoff_amplitude,
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
    fig.clear()

    # plot wave and the cutoff threshold
    plt.subplot(2, 1, 1)
    plt.plot(wave_data)

    for i in cutoff_amplitude:
        plt.plot([i] * len(wave_data), linestyle='--')
        # plt.plot([i] * len(wave_data), color='red', linestyle='--')
    plt.legend(['signal'] + ['cutoff ({} %)'.format(100 * i) for i in cutoff_ratio])
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
    for i in cutoff_amplitude:
        plt.plot([i] * len(wave_data), linestyle='--')
        # plt.plot([i] * len(wave_data), color='red', linestyle='--')
    plt.legend(['signal'] + ['cutoff ({} %)'.format(100 * i) for i in cutoff_ratio])
    plt.grid()
    plt.title('Samples sorted by amplitude')
    plt.xlim([0, len(wave_data)])
    plt.xlabel("Samples")
    plt.ylabel("Absolute amplitude")

    plt.savefig(path_to_save, bbox_inches='tight')


def visualize_noise_reduction(wave_data,
                              wave_data_denoised,
                              frame_rate: int,
                              path_to_save: str):
    fig = plt.figure(0, figsize=(6, 4))
    fig.clear()
    if not path_to_save.endswith('.png'):
        path_to_save = path_to_save + '.png'
    plt.plot(wave_data)
    plt.plot(wave_data_denoised)
    plt.legend(['source', 'reduced'])
    plt.grid()

    length_sec = int(len(wave_data)/frame_rate) + 1
    interval = min(10, length_sec)
    ind_1 = np.arange(0, length_sec+1, int(length_sec/interval))
    ind_2 = ind_1 * frame_rate
    plt.title('Nose reduction')
    plt.xticks(ind_2, ind_1)
    plt.xlim([0, len(wave_data)])
    plt.xlabel("Time (sec): total %0.2f" % (len(wave_data)/frame_rate))
    plt.ylabel("Amplitude")

    plt.savefig(path_to_save, bbox_inches='tight')
