import os
import numpy as np
from pydub import AudioSegment
from moviepy import editor
from .cutoff_methods import CutoffMethods
from ..util import create_log, combine_audio_video

VALID_FORMAT = ['mp3', 'wav', 'mp4']
LOG = create_log()


class AudioEditor:

    def __init__(self,
                 file_path,
                 cutoff_method: str='percentile',
                 max_sample_length: int=None):

        # load audio data
        self.__wave_array_np_list, self.__audio_format, self.__frame_rate, self.__sample_width, self.__channels, self.__video, self.__video_format = self.__load_audio(file_path)
        self.__cutoff_instance = CutoffMethods(cutoff_method)
        wave = self.__wave_array_np_list
        LOG.debug('audio info')
        LOG.debug(' * sample size     : %i' % len(wave))
        LOG.debug(' * sample sec      : %0.3f' % self.length_sec)
        LOG.debug(' * channel         : %i' % self.channels)
        LOG.debug(' * frame rate      : %i' % self.frame_rate)
        LOG.debug(' * sample width    : %i' % self.sample_width)
        LOG.debug(' * audio_amplitude : %i (max), %i (min)' % (np.max(wave), np.min(wave)))
        if self.__video is None:
            LOG.debug(' * no video')
        else:
            LOG.debug(' * video           : %s' % self.__video_format)
        if max_sample_length is not None and len(wave) > max_sample_length:
            raise ValueError('sample data exceeds max sample size: %i > %i' % (len(wave), max_sample_length))


    @staticmethod
    def __load_audio(file_path):
        """ Load audio file

         Parameter
        -----------
        file_path: str
            path to audio file, should be in VALID_FORMAT

         Return
        -----------
        wave_array_np_list: list of numpy array audio signal for each channel
        audio_format: audio format
        frame_rate: frame rate
        sample_width: sample width
        channels: channel size
        """
        # check file
        if not os.path.exists(file_path):
            raise ValueError('No file: %s' % file_path)

        # validate sound file (load as AudioSegment object
        video, video_format = None, None
        if file_path.endswith('.wav'):
            audio_format = 'wav'
            song = AudioSegment.from_wav(file_path)
        elif file_path.endswith('.mp3'):
            audio_format = 'mp3'
            song = AudioSegment.from_mp3(file_path)
        elif file_path.endswith('.mp4'):
            audio_format = 'mp3'
            video_format = 'mp4'
            song = AudioSegment.from_file(file_path)
            video = editor.VideoFileClip(file_path)
        else:
            raise ValueError('unknown format %s (valid format: %s)'% (file_path, VALID_FORMAT))

        # array.array object
        wave_array = song.get_array_of_samples()
        # numpyp array
        wave_array_np = np.array(wave_array)
        # if stereo (channel > 1)
        if song.channels != 1:
            if song.channels > 2:
                raise ValueError('audio has more than two channel: %i' % song.channels)
            wave_array_np_left = wave_array_np[0:len(wave_array_np):2]
            wave_array_np_right = wave_array_np[1:len(wave_array_np):2]
            wave_array_np_list = [wave_array_np_left, wave_array_np_right]
        else:
            wave_array_np_list = [wave_array_np]

        # information of audio file
        frame_rate = song.frame_rate
        sample_width = song.sample_width
        channels = song.channels

        return wave_array_np_list, audio_format, frame_rate, sample_width, channels, video, video_format

    def amplitude_clipping(self,
                           min_interval_sec: float,
                           ratio: float=1.0):
        """ Amplitude-based truncation. In given audio signal, where every sampling point has amplitude
        less than `min_amplitude` and the length is greater than `min_interval`, will be removed. Note that
        even if the audio has multi-channel, first channel will be processed.

         Parameter
        ---------------
        min_interval_sec: int
            minimum interval of cutoff (sec)
        """
        assert min_interval_sec > 0
        LOG.debug('start amplitude clipping')
        LOG.debug(' * min_interval_sec: %0.2f' % min_interval_sec)
        LOG.debug(' * ratio: %0.2f' % ratio)

        # pick up mono wave
        wave = self.__wave_array_np_list[0]

        min_amplitude = self.__cutoff_instance.get_cutoff_amp(wave, ratio=ratio)
        min_interval = int(min_interval_sec * self.__frame_rate)
        audio_signal_mask = np.array(np.abs(wave) > min_amplitude)
        LOG.debug('masked sample       : %i' % (wave.shape[0] - np.sum(audio_signal_mask)))

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
                    start = index[0]/self.__frame_rate
                    end = index[-1]/self.__frame_rate
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

        if not flg:
            keep_part_sec.append([i, self.length_sec])
        elif flg and min_interval < count:
            audio_signal_mask[index] = True
            keep_part_sec.append([i, self.length_sec])

        if len(keep_part_sec) > 0:
            __wave_array_np_list = []
            for wave in self.__wave_array_np_list:
                audio_signal_masked = wave[audio_signal_mask]
                __wave_array_np_list.append(audio_signal_masked)

            LOG.debug('processed: %i -> %i' % (len(self.__wave_array_np_list[0]), np.sum(audio_signal_mask)))
            assert len(__wave_array_np_list) == len(self.__wave_array_np_list)
            self.__wave_array_np_list = __wave_array_np_list

            # edit video
            if self.__video is not None:
                LOG.debug('process video')
                sub_videos = [self.__video.subclip(s, e) for s, e in keep_part_sec]
                LOG.debug(' * %i sub videos' % len(sub_videos))
                self.__video = editor.concatenate_videoclips(sub_videos)
        else:
            LOG.debug('nothing to process')

    def write(self, _file: str):
        """ write audio to file (format should be same as the input audio file) """

        def validate_path(__path):
            if os.path.exists(__path):
                os.remove(__path)
            if not os.path.exists(os.path.dirname(__path)):
                os.makedirs(os.path.dirname(__path), exist_ok=True)
            return __path

        if self.__video is not None:
            if not _file.endswith(self.__video_format):
                raise ValueError(
                    'file has %s, but given path indicate different format %s' % (self.__video_format, _file))
            _file_audio = validate_path(_file.replace('.%s' % self.__video_format, '.%s' % self.__audio_format))
            _file_video_no_audio = validate_path(
                _file.replace('.%s' % self.__video_format, '_no_audio.%s' % self.__video_format))
            _file_video = validate_path(_file)
        else:
            if not _file.endswith(self.__audio_format):
                raise ValueError(
                    'file has %s, but given path indicate different format %s' % (self.__audio_format, _file))
            _file_audio = validate_path(_file)
            _file_video = _file_video_no_audio = None

        LOG.debug(' * convert to serial form')
        wave_array_np_serial = np.reshape(np.array(self.__wave_array_np_list).T, [-1])

        LOG.debug(' * convert to AudioSegment object')
        audio_segment = AudioSegment(
            wave_array_np_serial.tobytes(),
            frame_rate=self.__frame_rate,
            sample_width=self.__sample_width,
            channels=self.__channels)

        LOG.debug(' * save audio to %s' % _file_audio)
        audio_segment.export(_file_audio, format=self.__audio_format)

        if self.__video is not None:
            LOG.debug(' * save video to %s' % _file_video_no_audio)
            self.__video.write_videofile(_file_video_no_audio)
            LOG.debug(' * embed audio to video, save to %s' % _file_video)
            combine_audio_video(video_file=_file_video_no_audio, audio_file=_file_audio, output_file=_file_video)

    @property
    def length_sec(self):
        return len(self.__wave_array_np_list[0]) / self.__frame_rate

    @property
    def wave_array(self):
        return self.__wave_array_np_list

    @property
    def audio_format(self):
        return self.__audio_format

    @property
    def frame_rate(self):
        return self.__frame_rate

    @property
    def sample_width(self):
        return self.__sample_width

    @property
    def channels(self):
        return self.__channels