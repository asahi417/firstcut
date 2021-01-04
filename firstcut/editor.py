""" Core audio/video editor """
import logging
from typing import List, Tuple
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
        self.file_path = file_path
        audio_stats, video_stats = load_file(self.file_path)
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
        """ Export audio/video file
        If `amplitude_clipping` has applied, the processed file will be exported, or if `noise_reduction` has applied,
        it will also be exported as a wav file. Note that (i) amplitude clipped will use raw audio, not denoised even
        if the clipping is performed over the denoised audio, since is clearer in many cases. (ii) For video, in the
        case where only noise_reduction has applied, it exports the denoised audio only and not combine with video.
        """
        # TODO: add an option to merge the denoised audio into video to export a new video with denoised audio
        if self.if_amplitude_clipping:
            logging.info('export edited file: {}'.format(export_file_prefix))
            return write_file(export_file_prefix=export_file_prefix, audio=self.audio_edit, video=self.video_edit,
                              audio_format=self.__audio_format, video_format=self.__video_format)
        if self.if_noise_reduction:
            logging.info('export denoised audio as .wav file: {}'.format(export_file_prefix))
            wave_signal = self.wave_array_np_list[0] / pow(2, 15)
            return write_file_wav(
                export_file_prefix=export_file_prefix, wave_signal=wave_signal, frame_rate=self.frame_rate)
        else:
            raise ValueError('no edit file found')

    def nmf_noise_reduction(self, noise_reference_interval: (List, Tuple), *args, **kwargs):
        """ Apply NMF based denoising to audio wave

         Parameter
        -------------
        noise_reference_interval: List
            (start, end) indicating the reference noise interval in the raw audio signal
        """
        logging.info('NMF noise reduction')
        assert len(noise_reference_interval) == 2,\
            'noise_reference_interval should be [start, end] but {}'.format(noise_reference_interval)

        # convert int16 to float32
        signal = self.wave_array_np_list[0] / pow(2, 15)
        s, e = noise_reference_interval
        signal_noise = self.wave_array_np_list[0][s:e] / pow(2, 15)
        mono = nmf_filter(signal, y_n=signal_noise, *args, **kwargs)
        denoised_waves = [mono] * len(self.wave_array_np_list)

        # revert float32 to int16
        self.wave_array_np_list = list(map(lambda w: (w * pow(2, 15)).astype(np.int16), denoised_waves))
        self.if_noise_reduction = True

    def noise_reduction(self,
                        min_interval_sec: float = 0.1,
                        cutoff_ratio: float = 0.5,
                        max_interval_ratio: int = 0.15,
                        n_iter: int = 1,
                        custom_noise_reference_interval: List = None):
        """ Noise Reduction based on unsupervised NMF: noise reference interval is identified based on
        `cutoff_amplitude` technique.

        signal = raw_signal
        while iteration < max_step:
            longest_silence_interval = amplitude_clipping(signal)
            signal = NMF_filter(signal, reference_noise = longest_silence_interval)

         Parameter
        -------------
        min_interval_sec: float
            see `amplitude_clipping`
        cutoff_ratio: float
            see `amplitude_clipping`
        max_interval_ratio: float
            stop noise reference identification loop if the length of noise signal exceed
            `max_interval_ratio * len(raw_signal)`
        n_iter: int
            number of iteration for noise reference identification
        noise_reference_interval: List
            (start, end) indicating the reference noise interval in the raw audio signal
            if this is given, noise reference identification isn't performed
        """

        if custom_noise_reference_interval is not None:
            self.nmf_noise_reduction(custom_noise_reference_interval)
            return

        max_interval = len(self.wave_array_np_list[0]) * max_interval_ratio
        i = 0
        while i < n_iter:
            logging.info('iterative_noise_reduction: iter {}/{}'.format(i + 1, n_iter))
            removal_interval = self.get_cutoff_interval(cutoff_ratio, min_interval_sec)
            if len(removal_interval) == 0:
                logging.info('re-run get_cutoff_interval as the interval was empty')
                cutoff_ratio = cutoff_ratio + (1 - cutoff_ratio) ** 2  # increase but not to exceed 1
                i += 0.2
            else:
                length = list(map(lambda x: x[1] - x[0], removal_interval))

                longest_interval = removal_interval[length.index(max(length))]
                interval = longest_interval[1] - longest_interval[0]
                if i > 0 and max_interval < interval:
                    logging.info('break as the interval is exceed max length: {} > {}'.format(interval, max_interval))
                    break
                self.nmf_noise_reduction(noise_reference_interval=longest_interval)
                i += 1

    def get_cutoff_interval(self, cutoff_ratio: float, min_interval_sec: float, in_second: bool = False):
        """ Get intervals to drop based on amplitude

         Parameter
        --------------
        min_interval_sec: float
            see `amplitude_clipping`
        cutoff_ratio: float
            see `amplitude_clipping`
        in_second: bool
            return signals_to_drop in second otherwise sample index

         Return
        ---------
        signals_to_drop: List
            a list of (start, end), indicating the intervals to drop
        """
        # get amplitude threshold with mono wave signal
        logging.info('get cutoff amplitude: (cutoff_ratio {}, min_interval: {})'.format(cutoff_ratio, min_interval_sec))
        min_amplitude = get_cutoff_amplitude(self.wave_array_np_list[0], cutoff_ratio=cutoff_ratio)
        min_interval = int(min_interval_sec * self.frame_rate)

        # get mask position: delete the chunk if its longer than min length
        logging.info('get masking position')
        mask_to_drop = np.array(np.abs(self.wave_array_np_list[0]) <= min_amplitude)
        mask_chunk = list(map(lambda x: list(x[1]), groupby(mask_to_drop)))
        length = list(map(lambda x: len(x), mask_chunk))
        partition = list(map(lambda x: [sum(length[:x]), sum(length[:x + 1])], range(len(length))))
        if in_second:
            # mask in audio file (second)
            signals_to_drop = list(map(
                lambda y: [float(y[2][0] / self.frame_rate), float(y[2][1] / self.frame_rate)],
                filter(lambda x: x[0][0] and x[1] >= min_interval, zip(mask_chunk, length, partition))))
        else:
            # raw signal in the removal interval
            signals_to_drop = list(map(
                lambda y: [y[2][0], y[2][1]],
                filter(lambda x: x[0][0] and x[1] >= min_interval, zip(mask_chunk, length, partition))))
        logging.info('{} masking position'.format(len(signals_to_drop)))
        return signals_to_drop

    def amplitude_clipping(self,
                           min_interval_sec: float = 0.12,
                           cutoff_ratio: float = 0.5,
                           crossfade_sec: float = None,
                           denoised_audio: bool = False):
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
        crossfade_sec = min_interval_sec / 2 if crossfade_sec is None else crossfade_sec
        assert min_interval_sec > 0 and crossfade_sec >= 0
        logging.info('start amplitude clipping')
        logging.info(' * min_interval_sec: {}'.format(min_interval_sec))
        logging.info(' * cutoff_ratio    : {}'.format(cutoff_ratio))
        logging.info(' * crossfade_sec   : {}'.format(crossfade_sec))
        # if denoised_audio:
        #     assert self.if_noise_reduction, 'no denoised signal found'
        #     export_file = self.file_path + '.denoised.wav'
        #     logging.info('export denoised audio: {}'.format(export_file))
        #     wave_signal = self.wave_array_np_list[0] / pow(2, 15)  # wav need to be float32
        #     write_file_wav(export_file_prefix=export_file, wave_signal=wave_signal, frame_rate=self.frame_rate)
        #     audio_stats, _ = load_file(export_file)
        #     (self.audio, self.wave_array_np_list, _, self.frame_rate, self.sample_width, self.channels) \
        #         = audio_stats

        signals_to_drop = self.get_cutoff_interval(cutoff_ratio, min_interval_sec, in_second=True)
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
