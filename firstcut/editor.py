""" Core audio/video editor

TODO:
- video file size compression without any editing
- allow specific span for no editing
- parallel processing for different configurations
- NMF for noise reduction
"""
import logging
from typing import List, Tuple
from itertools import groupby
from tqdm import tqdm

import numpy as np
from moviepy import editor

from .nmf import nmf_filter
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

    def plot_wave(self, path_to_save: str):
        """ Export plot of wave """
        cutoff_ratio = [0.75, 0.8, 0.85, 0.9, 0.95, 0.99]
        cutoff_amplitude = [self.get_cutoff_amplitude(self.wave_array_np_list[0], i) for i in cutoff_ratio]
        visualize_cutoff_amplitude(wave_data=self.wave_array_np_list[0],
                                   cutoff_ratio=cutoff_ratio,
                                   cutoff_amplitude=cutoff_amplitude,
                                   path_to_save=path_to_save,
                                   frame_rate=self.frame_rate)

    def export_file(self, export_file_prefix):
        """ Export audio/video file
        If `amplitude_clipping` has applied, the processed file will be exported, or if `noise_reduction` has applied,
        it will also be exported as a wav file. Note that (i) amplitude clipped will use raw audio, not denoised even
        if the clipping is performed over the denoised audio, since is clearer in many cases. (ii) For video, in the
        case where only noise_reduction has applied, it exports the denoised audio only and not combine with video.
        """
        return write_file(export_file_prefix=export_file_prefix, audio=self.audio, video=self.video,
                          audio_format=self.__audio_format, video_format=self.__video_format)

    def noise_reduction(self,
                        min_interval_sec: float = 0.125,
                        cutoff_ratio: float = 0.85,
                        max_interval_ratio: int = 0.15,
                        n_iter: int = 1,
                        export_plot: str = None,
                        export_audio: str = None):
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

        def nmf_noise_reduction(noise_reference_interval: (List, Tuple), *args, **kwargs):
            """ Apply NMF based denoising to audio wave

             Parameter
            -------------
            noise_reference_interval: List
                (start, end) indicating the reference noise interval in the raw audio signal
            """
            logging.info('NMF noise reduction')
            assert len(noise_reference_interval) == 2, \
                'noise_reference_interval should be [start, end] but {}'.format(noise_reference_interval)

            # convert int16 to float32
            signal = self.wave_array_np_list[0] / pow(2, 15)
            s, e = noise_reference_interval
            signal_noise = self.wave_array_np_list[0][s:e] / pow(2, 15)
            mono = nmf_filter(signal, y_n=signal_noise, *args, **kwargs)
            denoised_waves = [mono] * len(self.wave_array_np_list)

            # revert float32 to int16
            self.wave_array_np_list = list(map(lambda w: (w * pow(2, 15)).astype(np.int16), denoised_waves))

        wave_array_np_list_original = self.wave_array_np_list[0].copy()
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
                nmf_noise_reduction(noise_reference_interval=longest_interval)
                i += 1
        if export_plot is not None:
            logging.info('export plot to {}'.format(export_plot))
            visualize_noise_reduction(wave_data_denoised=self.wave_array_np_list[0],
                                      wave_data=wave_array_np_list_original,
                                      path_to_save=export_plot,
                                      frame_rate=self.frame_rate)
        if export_audio is not None:
            logging.info('export audio to {}'.format(export_audio))
            wave_signal = self.wave_array_np_list[0] / pow(2, 15)
            write_file_wav(export_file_prefix=export_audio, wave_signal=wave_signal, frame_rate=self.frame_rate)

    def amplitude_clipping(self,
                           min_interval_sec: float = 0.125,
                           cutoff_ratio: float = 0.85,
                           max_interval_ratio: int = 0.15,
                           n_iter: int = 1,
                           crossfade_sec: float = None,
                           apply_noise_reduction: bool = False):
        """ Amplitude-based truncation. In a given audio signal, where every sampling point has amplitude
        less than `min_amplitude` and the length is greater than `min_interval`, will be removed. Note that
        even if the audio has multi-channel, first channel will be processed.

         Parameter
        ---------------
        min_interval_sec: float
            minimum interval of cutoff (sec)
        cutoff_ratio: float
        crossfade_sec: float
        apply_noise_reduction: bool
            Apply noise reduction before editing.
        max_interval_ratio: float
            Noise reduction parameter.
        n_iter: float
            Noise reduction parameter.
        """
        crossfade_sec = min_interval_sec / 2 if crossfade_sec is None else crossfade_sec
        assert min_interval_sec > 0 and crossfade_sec >= 0
        logging.info('start amplitude clipping')
        logging.info(' * min_interval_sec: {}'.format(min_interval_sec))
        logging.info(' * cutoff_ratio    : {}'.format(cutoff_ratio))
        logging.info(' * crossfade_sec   : {}'.format(crossfade_sec))
        if apply_noise_reduction:
            self.noise_reduction(min_interval_sec=min_interval_sec, cutoff_ratio=cutoff_ratio,
                                 max_interval_ratio=max_interval_ratio, n_iter=n_iter)

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
            self.audio = audio
            if self.video is not None:
                assert video
                logging.info('process video: * {} sub videos'.format(len(video)))
                self.video = editor.concatenate_videoclips(video)

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
        min_amplitude = self.get_cutoff_amplitude(self.wave_array_np_list[0], cutoff_ratio=cutoff_ratio)
        min_interval = int(min_interval_sec * self.frame_rate)

        # get mask position: delete the chunk if its longer than min length
        logging.info('get masking position (usually the heaviest process within the entire pipeline)')
        mask_to_drop = np.array(np.abs(self.wave_array_np_list[0]) <= min_amplitude)
        mask_chunk = list(map(lambda x: list(x[1]), groupby(mask_to_drop)))
        length = list(map(lambda x: len(x), mask_chunk))
        partition = list(map(lambda x: [sum(length[:x]), sum(length[:x + 1])], range(len(length))))

        logging.info('{} mask chunks found'.format(len(mask_chunk)))
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

    @staticmethod
    def get_cutoff_amplitude(wave_data, cutoff_ratio: float = 0.5, method_type: str = 'ratio'):
        """ Get cutoff amplitude

         Parameter
        -----------
        wave_data: 1d nd.array
            mono wave signal
        cutoff_ratio: float
            cutoff percentile (higher removes more sample)

         Return
        -----------
        cutoff amplitude: float
        """
        assert np.ndim(wave_data) == 1
        if method_type == 'ratio':
            cutoff_ratio = np.clip(cutoff_ratio, 0.0, 1.0)
            single_array_sorted = np.sort(np.abs(wave_data))
            ind = int(np.floor(cutoff_ratio * len(wave_data)))
            val = single_array_sorted[min(ind, len(wave_data) - 1)]
            return int(val)
        else:
            raise ValueError('unknown `method_type`: {}'.format(method_type))
