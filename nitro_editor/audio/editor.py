import numpy as np
import soundfile as sf
import os


class Editor:

    @property
    def length_sec(self):
        return len(self.__signal) / self.__freq

    @property
    def freq(self):
        return self.__freq

    @property
    def audio(self):
        return self.__signal

    @property
    def signal_mask(self):
        return self.__signal_mask

    @property
    def keep_part_sec(self):
        return self.__keep_part_sec

    def __init__(self, file_path):
        assert file_path.endswith('.wav')
        if not os.path.exists(file_path):
            raise ValueError('No file at: %s' % file_path)
        # load wav audio
        self.__signal, self.__freq = sf.read(file_path)
        if len(self.__signal.shape) != 1:
            self.__signal = self.__signal[:, 0]

        self.__signal_mask = None
        self.__keep_part_sec = None

    def amplitude_clipping(self,
                           min_amplitude: float,
                           min_interval_sec: int):
        """ Amplitude-based truncation. In given audio signal, where every sampling point has amplitude
            less than `min_amplitude` and the length is greater than `min_interval`, will be removed.


         Parameter
        ---------------
        min_amplitude: float
            minimum amplitude to cutoff
        min_interval_sec: int
            minimum interval of cutoff (sec)
        """

        assert min_amplitude > 0
        assert min_interval_sec > 0

        min_interval = int(min_interval_sec * self.__freq)
        audio_signal_mask = (np.abs(self.__signal) > min_amplitude)

        flg = False
        count = 0
        index = []
        keep_part_sec = []
        i = 0
        for n, m in enumerate(audio_signal_mask):
            if m and flg:
                if min_interval > count:
                    audio_signal_mask[index] = True
                else:
                    # exclusion part
                    start = index[0]/self.freq
                    end = index[-1]/self.freq
                    assert end >= start
                    if start != i:
                        keep_part_sec.append([i, start])
                    i = end

                count = 0
                flg = False
                index = []
            if not m:
                flg = True
                count += 1
                index.append(n)

        # print(self.length_sec)
        if not flg:
            keep_part_sec.append([i, self.length_sec])
        elif flg and min_interval < count:
            audio_signal_mask[index] = True
            keep_part_sec.append([i, self.length_sec])

        audio_signal_masked = self.__signal[audio_signal_mask]
        self.__signal = audio_signal_masked
        self.__signal_mask = audio_signal_mask
        self.__keep_part_sec = keep_part_sec

    def write(self, _file):
        assert _file.endswith('.wav')
        if os.path.exists(_file):
            os.remove(_file)
        elif not os.path.exists(os.path.dirname(_file)):
                os.makedirs(os.path.dirname(_file), exist_ok=True)
        sf.write(_file, self.__signal, self.__freq, 'PCM_24')
