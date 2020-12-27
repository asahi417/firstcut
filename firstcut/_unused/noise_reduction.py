from scipy.signal import butter, lfilter


VALID_METHOD_TYPES = ['bandpass']

__all__ = ['NoiseReduction']


class NoiseReduction:

    def __init__(self,
                 method_type: str = 'bandpass'):

        if method_type not in VALID_METHOD_TYPES:
            raise ValueError('unknown `method_type`: %s not in %s' % (method_type, VALID_METHOD_TYPES))
        self.__method_type = method_type

    def reduction(self,
                  wave: list,
                  frame_rate: int,
                  cutoff: list = None,
                  order: int = 6,
                  return_filter: bool = False):
        if self.__method_type in ['bandpass']:
            single_chanel_wave = wave[0]
            return self.butter_bandpass_filter(single_chanel_wave,
                                               frame_rate=frame_rate,
                                               cutoff=cutoff,
                                               order=order,
                                               return_filter=return_filter)
        else:
            raise ValueError('unknown `method_type`: %s not in %s' % (self.__method_type, VALID_METHOD_TYPES))

    @staticmethod
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

    def butter_bandpass_filter(self,
                               data,
                               frame_rate: int,
                               cutoff: list = None,
                               order: int = 6,
                               return_filter: bool=False):

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
        if cutoff is None:
            return data
        if len(cutoff) != 2:
            raise ValueError('cutoff shoud be [low, high]')

        lowcut, highcut = cutoff
        [b, a] = self.butter_bandpass(frame_rate, lowcut, highcut, order)
        y = lfilter(b, a, data)
        if return_filter:
            return y, [b, a]
        else:
            return y
