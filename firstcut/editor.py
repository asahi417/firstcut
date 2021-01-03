""" Core audio/video editor """
import logging
from itertools import groupby
from tqdm import tqdm

import numpy as np
from moviepy import editor

from .nmf import nmf_filter
from .cutoff_amplitude import get_cutoff_amplitude
from .util import write_file, load_file, write_file_wav
from .visualization import visualize_noise_reduction, visualize_cutoff_amplitude

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
__all__ = 'Editor'


class Editor:
    """ Core audio/video editor:
    - (i) split video into audio and movie
    - (ii) process separately
    - (iii) combine `pydub.AudioSegment` for audio interface, and `moviepy.editor` for movie interface """

    def __init__(self, file_path: str, max_sample_length: int = None):
        """ Core audio/video editor

         Parameter
        -------------
        file_path: str
            absolute path to file name
        max_sample_length: int
            set a max sample length (to avoid being clogged by extremely long audio file)
        """
        audio_stats, video_stats = load_file(file_path)
        (self.audio, self.wave_array_np_list, self.__audio_format, self.frame_rate, self.sample_width, self.channels) \
            = audio_stats
        self.video, self.__video_format, self.is_mov = video_stats
        self.length = len(self.wave_array_np_list[0])

        self.length_sec = len(self.audio) / 1000  # self.length / self.frame_rate
        self.format = self.__audio_format if self.video is None else self.__video_format
        logging.info('audio info')
        logging.info(' * sample size   : {}'.format(self.length))
        logging.info(' * sample sec    : {}'.format(self.length_sec))
        logging.info(' * channel       : {}'.format(self.channels))
        logging.info(' * frame rate    : {}'.format(self.frame_rate))
        logging.info(' * sample width  : {}'.format(self.sample_width))
        logging.info(' * audio_amp     : {} (max), {} (min)'.format(
            np.max(self.wave_array_np_list), np.min(self.wave_array_np_list)))
        if self.video is None:
            logging.info(' * no video')
        else:
            logging.info(' * video         : {}'.format(self.__video_format))
        if max_sample_length is not None and self.length > max_sample_length:
            raise ValueError('sample data exceeds max sample size: {} > {}'.format(self.length, max_sample_length))

        self.wave_array_np_list_raw = self.wave_array_np_list.copy()
        self.audio_edit = None
        self.video_edit = None
        self.cutoff_ratio = None
        self.if_noise_reduction = False
        self.if_amplitude_clipping = False

    def noise_reduction(self,
                        method: str = 'nmf',
                        all_channel: bool = False,
                        *args, **kwargs):
        """ Apply denoising to audio wave

         Parameter
        -------------
        method: str
            'nmf' or 'bandpass'
        all_channel: bool
            to apply all channel, otherwise to apply only on mono wave
        """
        logging.info('noise reduction: {}'.format(method))

        # convert int16 to float32
        float_waves = [w / pow(2, 15) for w in self.wave_array_np_list]
        if method == 'nmf':
            mono = nmf_filter(float_waves[0], frame_rate=self.frame_rate, *args, **kwargs)
        else:
            raise ValueError('unknown method: {}}'.format(method))

        denoised_waves = [mono] * len(float_waves)

        # revert float32 to int16
        self.wave_array_np_list = list(map(lambda w: (w * pow(2, 15)).astype(np.int16), denoised_waves))

        self.if_noise_reduction = True

    def plot(self, path_to_save: str, figure_type: str = 'noise_reduction'):
        shared = {'wave_data': self.wave_array_np_list_raw[0], 'path_to_save': path_to_save,
                  'frame_rate': self.frame_rate}
        if figure_type == 'noise_reduction':
            assert self.if_noise_reduction, 'noise_reduction is not applied yet'
            visualize_noise_reduction(wave_data_denoised=self.wave_array_np_list[0], **shared)
        elif figure_type == 'amplitude_clipping':
            assert self.if_amplitude_clipping, 'amplitude_clipping is not applied yet'
            visualize_cutoff_amplitude(self.cutoff_ratio, **shared)
        else:
            raise ValueError('unknown figure type: {}'.format(figure_type))
        logging.info('plot saved at {}'.format(path_to_save))

    def export(self, export_file_prefix):
        if self.if_amplitude_clipping:
            logging.info('export edited file')
            return write_file(export_file_prefix=export_file_prefix, audio=self.audio_edit, video=self.video_edit,
                              audio_format=self.__audio_format, video_format=self.__video_format)
        elif self.if_noise_reduction:
            logging.info('export denoised audio as .wav file')
            wave_signal = self.wave_array_np_list[0] / pow(2, 15)
            return write_file_wav(
                export_file_prefix=export_file_prefix, wave_signal=wave_signal, frame_rate=self.frame_rate)
        else:
            raise ValueError('no edit file found')

    def amplitude_clipping(self,
                           min_interval_sec: float,
                           cutoff_ratio: float = 0.5,
                           crossfade_sec: float = None):
        """ Amplitude-based truncation. In a given audio signal, where every sampling point has amplitude
        less than `min_amplitude` and the length is greater than `min_interval`, will be removed. Note that
        even if the audio has multi-channel, first channel will be processed.

         Parameter
        ---------------
        min_interval_sec: float
            minimum interval of cutoff (sec)
        cutoff_ratio: float
        crossfade_sec: float
        """
        crossfade_sec = min_interval_sec/2 if crossfade_sec is None else crossfade_sec
        assert min_interval_sec > 0 and crossfade_sec >= 0
        logging.info('start amplitude clipping')
        logging.info(' * min_interval_sec: {}'.format(min_interval_sec))
        logging.info(' * cutoff_ratio    : {}'.format(cutoff_ratio))
        logging.info(' * crossfade_sec   : {}'.format(crossfade_sec))

        # get amplitude threshold with mono wave signal
        logging.info('get cutoff amplitude')
        min_amplitude = get_cutoff_amplitude(self.wave_array_np_list[0], cutoff_ratio=cutoff_ratio)
        min_interval = int(min_interval_sec * self.frame_rate)

        # get mask position: delete the chunk if its longer than min length
        logging.info('get masking position')
        mask_to_drop = np.array(np.abs(self.wave_array_np_list[0]) <= min_amplitude)
        mask_chunk = list(map(lambda x: list(x[1]), groupby(mask_to_drop)))
        length = list(map(lambda x: len(x), mask_chunk))
        partition = list(map(lambda x: [sum(length[:x]), sum(length[:x + 1])], range(len(length))))
        signals_to_drop = list(map(
            lambda y: (float(y[2][0] / self.frame_rate), float(y[2][1] / self.frame_rate)),
            filter(lambda x: x[0][0] and x[1] >= min_interval, zip(mask_chunk, length, partition))))
        logging.info('{} masking position'.format(len(signals_to_drop)))

        logging.info('start combining clips')
        start, end = signals_to_drop.pop(0)
        cf_sec = min(start/1000, min((end - start) / 2, crossfade_sec))
        cf_sec = 0 if cf_sec < 0.001 else cf_sec  # clip too small value
        audio = self.audio[0: (start + cf_sec) * 1000]
        if self.video is not None:
            video = [self.video.subclip(0, start + cf_sec / 2)]
        else:
            video = None
        pointer = end
        prev_cf_sec = cf_sec

        for i in tqdm(list(range(len(signals_to_drop)))):

            start, end = signals_to_drop[i]
            cf_sec = min((end - start) / 2, crossfade_sec)  # clip cf smaller than crossfade_sec
            cf_sec = min((len(audio) + start - pointer) / 1000, cf_sec)  # clip cf smaller than tmp audio
            cf_sec = min((self.length_sec - end) / 1000, cf_sec)  # clip cf smaller than remaining audio
            cf_sec = 0 if cf_sec < 0.001 else cf_sec  # clip too small value
            audio = audio.append(self.audio[(pointer - prev_cf_sec) * 1000:(start + cf_sec) * 1000],
                                 crossfade=prev_cf_sec * 1000)
            if self.video is not None:
                video.append(self.video.subclip(pointer - prev_cf_sec / 2, start + cf_sec / 2))
            prev_cf_sec = cf_sec
            pointer = end

        if pointer != self.length_sec:
            audio = audio.append(self.audio[(pointer - prev_cf_sec) * 1000:self.length_sec * 1000],
                                 crossfade=prev_cf_sec * 1000)
            if self.video is not None:
                video.append(self.video.subclip((pointer - prev_cf_sec/2), self.length_sec))

        assert audio is not None
        logging.info('complete editing: {} sec -> {} sec'.format(self.length_sec, len(audio)/1000))
        if self.length_sec != len(audio)/1000:
            self.audio_edit = audio
            if self.video is not None:
                assert video
                logging.info('process video: * {} sub videos'.format(len(video)))
                self.video_edit = editor.concatenate_videoclips(video)
        self.cutoff_ratio = cutoff_ratio
        self.if_amplitude_clipping = True

    @property
    def file_identifier(self):
        """ file identifier """
        if self.video is not None:
            return self.__video_format
        else:
            return self.__audio_format
