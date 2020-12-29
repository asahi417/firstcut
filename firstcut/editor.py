""" Core audio/video editor """
import logging
from itertools import groupby
from tqdm import tqdm

import numpy as np
from moviepy import editor

from .cutoff_amplitude import get_cutoff_amplitude
from .ffmpeg import write_file, load_file

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

        self.audio_edit = None
        self.video_edit = None

    def export(self, export_file_prefix):
        assert self.audio_edit is not None, 'no edit file found'
        return write_file(export_file_prefix=export_file_prefix, audio=self.audio_edit, video=self.video_edit,
                          audio_format=self.__audio_format, video_format=self.__video_format)

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

    @property
    def is_edited(self):
        return True if self.audio_edit is not None else False

    @property
    def file_identifier(self):
        """ file identifier """
        if self.video is not None:
            return self.__video_format
        else:
            return self.__audio_format
