import numpy as np
import soundfile as sf
# from matplotlib import pyplot as plt
# import seaborn

VALID_FORMAT = ['wav']


def load_audio(_file: str,
               resampling_freq: int=None,
               file_format: str='wav'):
    """ Load sound file

     Parameter
    ----------------
    _file: str
        file path to be loaded
    resampling_freq: int
        Re-sampling frequency. Audio data will be re-sampled by the frequency if this is given.
    file_format: str
        format of audio file

     Return
    ----------------
    audio_signal: ndarray (sample size, )
        audio signal
    freq: frequency of audio signal
    """
    if file_format == 'wav':
        assert _file.endswith('.wav')
        audio_signal, data_fs = sf.read(_file)
        if resampling_freq is not None:
            assert type(resampling_freq) == int
            audio_signal = audio_signal[::np.int(np.floor(data_fs / resampling_freq))]
            freq = resampling_freq
        else:
            freq = data_fs
        # make sound mono
        if len(audio_signal.shape) != 1:
            audio_signal = audio_signal[:, 0]
        return audio_signal, freq
    else:
        raise ValueError('%s is not valid format: shoud be one of %s' % (file_format, str(VALID_FORMAT)))


def write_audio(_file: str,
                audio_signal,
                frequency: int,
                file_format: str='wav'):

    if file_format == 'wav':
        assert _file.endswith('.wav')
        sf.write(_file, audio_signal, frequency, 'PCM_24')
    else:
        raise ValueError('%s is not valid format: shoud be one of %s' % (file_format, str(VALID_FORMAT)))
