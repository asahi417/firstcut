import numpy as np
import soundfile as sf
import os
import logging
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


def create_log(out_file_path=None):
    """ Logging
        If `out_file_path` is None, only show in terminal
        or else save log file in `out_file_path`
    Usage
    -------------------
    logger.info(message)
    logger.error(error)
    """

    # handler to record log to a log file
    if out_file_path is not None:
        if os.path.exists(out_file_path):
            os.remove(out_file_path)
        logger = logging.getLogger(out_file_path)

        if len(logger.handlers) > 1:  # if there are already handler, return it
            return logger
        else:
            logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter("H1, %(asctime)s %(levelname)8s %(message)s")

            handler = logging.FileHandler(out_file_path)
            handler.setFormatter(formatter)
            logger.addHandler(handler)

            logger_stream = logging.getLogger()
            # check if some stream handlers are already
            if len(logger_stream.handlers) > 0:
                return logger
            else:
                handler = logging.StreamHandler()
                handler.setFormatter(formatter)
                logger.addHandler(handler)

                return logger
    else:
        # handler to output
        handler = logging.StreamHandler()
        logger = logging.getLogger()

        if len(logger.handlers) > 0:  # if there are already handler, return it
            return logger
        else:  # in case of no, make new output handler
            logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter("H1, %(asctime)s %(levelname)8s %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            return logger
