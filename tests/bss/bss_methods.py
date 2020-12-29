""" Collection of functions to BSS methods """

import numpy as np
# only use nmf...?
from scipy.signal import butter, lfilter, freqz
import librosa
from pydub import AudioSegment
import ssnmf

VALID_METHOD_TYPES = ['nmf']

class BSSMethods:

    def __init__(self, method_type='nmf'):
        if method_type not in VALID_METHOD_TYPES:
            raise ValueError('unknown `method_type`: %s not in %s' % (method_type, VALID_METHOD_TYPES))
        self.__method_type = method_type

    def get_clean_signal(self, original_data, noise_data):
        if self.__method_type in ['nmf']:
            if self.__method_type is 'nmf':
                return self.__ssnmf(original_data, noise_data)
            
    @staticmethod
    def __ssnmf(data, noise):
        """ nmf """
        y_out = ssnmf.SSNMF(data, noise)
        return y_out
