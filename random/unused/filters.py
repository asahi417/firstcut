import numpy as np


def amplitude_filter(audio_signal,
                     min_amplitude: float,
                     min_interval: int):
    """ Amplitude-based truncation. In given audio signal, where every sampling point has amplitude
    less than `min_amplitude` and the length is greater than `min_interval`, will be removed.


     Parameter
    ---------------
    audio_signal: ndarray
        audio signal, which is 1-dim numpy array
    min_amplitude: float
        minimum amplitude to cutoff
    min_interval: int
        minimum interval (in terms of sampling point) of cutoff

     Return
    ---------------
    audio_signal_masked: ndarray
        modified audio signal
    audio_signal_mask: ndarray
        boolean mask
    """

    assert min_amplitude > 0
    assert min_interval > 0

    audio_signal_mask = (np.abs(audio_signal) > min_amplitude)

    flg = False
    count = 0
    index = []
    for n, m in enumerate(audio_signal_mask):
        if m and flg:
            if min_interval > count:
                audio_signal_mask[index] = True
            count = 0
            flg = False
            index = []
        if not m:
            flg = True
            count += 1
            index.append(n)
    if flg and min_interval < count:
        audio_signal_mask[index] = True
    audio_signal_masked = audio_signal[audio_signal_mask]
    return audio_signal_masked, audio_signal_mask

