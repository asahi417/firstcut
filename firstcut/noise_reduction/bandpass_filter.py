from typing import List
from scipy.signal import butter, lfilter


def butter_bandpass(frame_rate: float,
                    lowcut: float = None,
                    highcut: float = None,
                    order: int = 5):
    """ Filter coefficient
    - Bandpass (lowcut < frequency < highcut)
    - Lowpass (frequency < lowcut)
    - Hihgpass (highcut < frequency)


     Parameter
    ------------
    frame_rate: float
        sampling frequency
    lowcut: float
        cut off frequency (low)
    highcut: float
        cut off frequency (high)

     Return
    ------------
    filter coefficient a
    filter coefficient b
    """
    nyq = 0.5 * frame_rate
    if lowcut is None and highcut is None:
        return None
    elif lowcut is None and highcut is not None:
        cutoff = highcut / nyq
        [b, a] = butter(order, [cutoff], btype='high')
    elif lowcut is not None and highcut is None:
        cutoff = lowcut / nyq
        [b, a] = butter(order, [cutoff], btype='low')
    else:
        low = lowcut / nyq
        high = highcut / nyq
        [b, a] = butter(order, [low, high], btype='band')
    return b, a


def bandpass_filter(data,
                    frame_rate: int,
                    cutoff: List,
                    order: int = 6):
    """ Bandpass filter

    - Bandpass (lowcut < frequency < highcut)
    - Lowpass (frequency < lowcut)
    - Hihgpass (highcut < frequency)

     Parameter
    ------------------
    data:
        target data
    frame_rate: float
        sampling frequency
    lowcut: float
        cut off frequency (low)
    highcut: float
        cut off frequency (high)
    order: int
        filter order

     Return
    ------------------
    filtered signal
    """
    if len(cutoff) != 2:
        raise ValueError('cutoff shoud be [low, high]')

    lowcut, highcut = cutoff
    b, a = butter_bandpass(frame_rate, lowcut, highcut, order)
    y = lfilter(b, a, data)
    return y, [b, a]
