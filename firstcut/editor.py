""" Audio editor with cross fade """
import logging
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')

import numpy as np
from moviepy import editor

from .cutoff_methods import CutoffMethods
from .ffmpeg import write_file, load_file

__all__ = ('AudioEditor', 'VALID_FORMAT')

# MOV (Apple's movie format), m4a (Apple's sound file format), mov file will be converted to mp4 file
VALID_FORMAT = ['mp3', 'wav', 'm4a', 'mp4', 'mov', 'MP3', 'WAV', 'M4A', 'MP4', 'MOV']


class AudioEditor:
    """ Core audio/video editor:
    - (i) split video into audio and movie
    - (ii) process separately
    - (iii) combine `pydub.AudioSegment` for audio interface, and `moviepy.editor` for movie interface """

    def __init__(self,
                 file_path,
                 cutoff_method: str = 'percentile',
                 max_sample_length: int = None):
        """ Audio based video editor

         Parameter
        -------------
        file_path: str
            absolute path to file name
        cutoff_method: str
            cutoff method
        max_sample_length: int
            max sample length for audio file
        """
        audio, audio_stats, self.video, video_stats = load_file(file_path)
        self.audio, self.wave_array_np_list = audio
        self.__audio_format, self.frame_rate, self.sample_width, self.channels = audio_stats
        self.__video_format, self.is_mov = video_stats
        self.__cutoff_instance = CutoffMethods(cutoff_method)
        self.length = len(self.wave_array_np_list[0])

        self.length_sec = self.length / self.frame_rate
        self.format = self.__audio_format if self.video is None else self.__video_format
        logging.debug('audio info')
        logging.debug(' * sample size   : {}'.format(self.length))
        logging.debug(' * sample sec    : {}'.format(self.length_sec))
        logging.debug(' * channel       : {}'.format(self.channels))
        logging.debug(' * frame rate    : {}'.format(self.frame_rate))
        logging.debug(' * sample width  : {}'.format(self.sample_width))
        logging.debug(' * audio_amp     : {} (max), {} (min)'.format(
            np.max(self.wave_array_np_list), np.min(self.wave_array_np_list)))
        if self.video is None:
            logging.debug(' * no video')
        else:
            logging.debug(' * video         : {}'.format(self.__video_format))
        if max_sample_length is not None and self.length > max_sample_length:
            raise ValueError('sample data exceeds max sample size: {} > {}'.format(self.length, max_sample_length))

    def export(self, export_file_prefix):
        return write_file(
            export_file_prefix=export_file_prefix,
            audio=self.audio, video=self.video,
            audio_format=self.__audio_format, video_format=self.__video_format)

    def amplitude_clipping(self,
                           min_interval_sec: float,
                           ratio: float = 1.0,
                           crossfade_sec: float = 0.1):
        """ Amplitude-based truncation. In given audio signal, where every sampling point has amplitude
        less than `min_amplitude` and the length is greater than `min_interval`, will be removed. Note that
        even if the audio has multi-channel, first channel will be processed.

         Parameter
        ---------------
        min_interval_sec: int
            minimum interval of cutoff (sec)
        """
        assert min_interval_sec > 0 and crossfade_sec >= 0
        logging.debug('start amplitude clipping')
        logging.debug(' * min_interval_sec: %0.2f' % min_interval_sec)
        logging.debug(' * ratio           : %0.2f' % ratio)
        logging.debug(' * crossfade_sec   : %0.2f' % crossfade_sec)

        # pick up mono wave
        min_amplitude = self.__cutoff_instance.get_cutoff_amp(self.wave_array_np_list[0], ratio=ratio)
        min_interval = int(min_interval_sec * self.frame_rate)
        audio_signal_mask = np.array(np.abs(self.wave_array_np_list[0]) > min_amplitude)  # for audio edit
        logging.debug('masked sample       : %i' % (self.length - np.sum(audio_signal_mask)))

        flg_deleting = False
        index = []
        pointer = 0
        deleted_sec = 0
        editing_audio = None
        editing_video = []
        last_edit_end = None
        last_cf_sec = 0
        prev_edit_point = None

        def _edit(_audio, _video, _last_edit_end, _last_cf_sec, _prev_edit_point, _current_edit_point=None):
            """ Edit with cross fade
            eg) sample: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], part_a: [1, 2, 3, 4], part_b: [9, 10, 11, 12]
            audio_process = part_a + cross_fade([5, 6], [7, 8]) + part_b = [1, 2, 3, 4, cf, cf, 9, 10, 11, 12]
            video_process = part_a + buffer_a + buffer_b + part_b = [1, 2, 3, 4, 5, 6, 9, 10, 11, 12]
                * buffer_a = 5, buffer_b = 8
                * len(audio_process) == len(video_process)
                * no overlap
                * slicing is done by milliseconds
            """
            if _current_edit_point is None:  # the final edit point
                if _prev_edit_point is not None:
                    start, end = _prev_edit_point
                    if _audio is None:  # only single keep part
                        _audio = self.audio[start * 1000:end * 1000]
                        if self.video is not None:
                            _video.append(self.video.subclip(start, end))
                    else:
                        _audio = _audio.append(self.audio[(start - _last_cf_sec) * 1000:end * 1000],
                                               crossfade=_last_cf_sec * 1000)
                        if self.video is not None:
                            _video.append(self.video.subclip(start - _last_cf_sec/2, end))
                return _audio, _video, 0, None, None

            start, end = _current_edit_point
            assert start <= end
            if end == start or (self.length_sec == end and start == 0):  # ignore the edit point
                return _audio, _video, _last_edit_end, _last_cf_sec, _prev_edit_point

            if _prev_edit_point is None:  # the first edit point
                return _audio, _video, 0, None, _current_edit_point

            p_start, p_end = _prev_edit_point
            max_no_overlap_crossfade_sec = np.floor((p_start - _last_edit_end)/2)
            _cf_sec = min(max_no_overlap_crossfade_sec, crossfade_sec)

            if _audio is None:  # the second edit point
                _audio = self.audio[p_start * 1000:(p_end + _cf_sec) * 1000]
                if self.video is not None:
                    _video.append(self.video.subclip(p_start, p_end + _cf_sec / 2))
            else:  # for other edit points
                _clip = self.audio[(p_start - _last_cf_sec) * 1000:(p_end + _cf_sec) * 1000]
                _audio = _audio.append(_clip, crossfade=_last_cf_sec * 1000)
                if self.video is not None:
                    _video.append(self.video.subclip(p_start - _last_cf_sec / 2, p_end + _cf_sec / 2))

            return _audio, _video, p_end, _cf_sec, _current_edit_point

        # loop for all the sample to get parts to keep
        for n, bool_mask in enumerate(audio_signal_mask):
            if bool_mask and flg_deleting:  # finish deleting chunk
                if min_interval <= len(index):  # delete the chunk if its longer than min length
                    delete_from = index[0] / self.frame_rate
                    delete_to = index[-1] / self.frame_rate
                    editing_audio, editing_video, last_edit_end, last_cf_sec, prev_edit_point = _edit(
                        editing_audio, editing_video, last_edit_end, last_cf_sec, prev_edit_point,
                        _current_edit_point=[pointer, delete_from])
                    pointer = delete_to
                    deleted_sec += delete_to - delete_from
                flg_deleting = False
                index = []
            if not bool_mask:
                flg_deleting = True
                index.append(n)

        if flg_deleting and min_interval <= len(index):
            end_point = index[0] / self.frame_rate
        else:
            end_point = self.length_sec

        editing_audio, editing_video, last_edit_end, last_cf_sec, prev_edit_point = _edit(
            editing_audio, editing_video, last_edit_end, last_cf_sec, prev_edit_point,
            _current_edit_point=[pointer, end_point])

        # final edit
        editing_audio, editing_video, _, _, _ = _edit(
            editing_audio, editing_video, last_edit_end, last_cf_sec, prev_edit_point,
            _current_edit_point=None)

        if editing_audio is None:
            logging.debug('nothing to process')
            return False
        else:
            logging.debug('processed: remove %0.3f sec (original audio was %0.2f sec)' % (deleted_sec, self.length_sec))
            # if fadeout_sec is not None:
            #     self.audio = editing_audio.fade_out(fadeout_sec)
            # else:
            self.audio = editing_audio

            # edit video
            if self.video is not None:
                logging.debug('process video: * %i sub videos' % len(editing_video))
                self.video = editor.concatenate_videoclips(editing_video)
            return True

    @property
    def file_identifier(self):
        """ file identifier """
        if self.video is not None:
            return self.__video_format
        else:
            return self.__audio_format


    # def vis_amplitude_clipping(self,
    #                            ratio: float = 1.0,
    #                            path_to_save: str = None):
    #     wave = self.wave_array_np_list[0]
    #     self.__cutoff_instance.visualize_cutoff_threshold(
    #         wave_data=wave,
    #         frame_rate=self.frame_rate,
    #         ratio=ratio,
    #         path_to_save=path_to_save
    #     )
