""" FFMPEG and relevant audio/video operating tools """
import os
import subprocess
import logging
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')

import numpy as np
from pydub import AudioSegment
from moviepy import editor


__all__ = ('combine_audio_video', 'mov_to_mp4', 'load_file', 'write_file')


def exe_shell(command: str, exported_file: str = None):
    """ Execute shell command

     Parameter
    -------------
    command: str
        shell command
    exported_file: str
        path to file produced by the command for error handling
    """
    logging.info("execute `{}`".format(command))
    try:
        args = dict(stderr=subprocess.STDOUT, shell=True, timeout=600, universal_newlines=True)
        log = subprocess.check_output(command, **args)
        logging.info("log\n{}".format(log))
    except subprocess.CalledProcessError as exc:
        if exported_file and os.path.exists(exported_file):
            # clear possibly broken file out
            os.system('rm -rf {}'.format(exported_file))
        raise ValueError("fail to execute command `{}`:\n {}\n {}".format(command, exc.returncode, exc.output))


def mov_to_mp4(video_file: str, overwrite: bool = False):
    """ Convert sample.MOV to sample.mp4 by ffmpeg: (the converted mp4 doesn't have audio)
    `ffmpeg -i sample.MOV -vcodec h264 -acodec mp2 sample.mp4`

     Parameter
    --------------------
    video_file: str
        path to target MOV file eg) sample.MOV
    overwrite: bool
        overwrite if it exists

     Return
    --------------------
    _file: str
        produced file eg) sample.mp4
    """
    _id = video_file.split('.')[-1]
    output_file = '.'.join(video_file.split('.')[:-1])
    if _id not in ['mov', 'MOV']:
        raise ValueError('{} is not MOV/mov format'.format(video_file))
    output_file += '.mp4'
    command = "ffmpeg -i {} -vcodec h264 -acodec mp2 {}".format(video_file, output_file)
    if os.path.exists(output_file):
        logging.info('found file at {}'.format(output_file))
        if overwrite:
            logging.info('found file at {0}: going to overwrite it'.format(output_file))
            os.system('rm -rf {}'.format(output_file))
        else:
            logging.info('found file at {0}: returning it'.format(output_file))
            return output_file
    exe_shell(command, exported_file=output_file)
    assert os.path.exists(output_file), 'file has not produced at {}'.format(output_file)
    return output_file


def combine_audio_video(video_file: str, audio_file: str, output_file: str):
    """ Combine audio data and video by ffmpeg:
    `ffmpeg -i sample.mp4 -i sample.mp3 -vcodec copy sample_combined.mp4`

     Parameter
    --------------------
    video_file: str
        path to target mp4 video file
    audio_file: str
        path to save audio wav or mp3 audio file
    output_file: str
        export file path
    """

    if not video_file.endswith('.mp4'):
        raise ValueError('unknown video format: {}'.format(video_file))
    if not (audio_file.endswith('.wav') or audio_file.endswith('.mp3')):
        raise ValueError('unknown audio format: {}'.format(audio_file))

    if not os.path.exists(video_file):
        raise ValueError('No video file at: {}'.format(video_file))

    if os.path.exists(output_file):
        os.system('rm -rf {}'.format(output_file))

    command = "ffmpeg -i {} -i {} -vcodec copy {}".format(video_file, audio_file, output_file)
    exe_shell(command, exported_file=output_file)
    assert os.path.exists(output_file), 'file has not produced at {}'.format(output_file)


def load_file(file_path):
    """ Load audio/video file

     Parameter
    -----------
    file_path: str
        path to audio/video file

     Return
    -----------
    audio: tuple
        pydub.AudioSegment instance of audio,
        list of numpy array audio signal for each channel,
        audio_format, frame_rate, sample_width, channels, channel size
    video: tuple
        moviepy.editor instance of video,
        video_format, convert_mov (bool if mov file has been converted)
    """

    # check file
    assert os.path.exists(file_path), 'No file: {}'.format(file_path)
    logging.info('loading {}'.format(file_path))

    # validate sound file (load as AudioSegment object
    video, video_format, convert_mov = None, None, False
    if file_path.endswith('.wav') or file_path.endswith('.WAV'):
        audio_format = 'wav'
        audio = AudioSegment.from_wav(file_path)
    elif file_path.endswith('.mp3') or file_path.endswith('.MP3'):
        audio_format = 'mp3'
        audio = AudioSegment.from_mp3(file_path)
    elif file_path.endswith('.m4a') or file_path.endswith('.M4A'):
        audio_format = 'm4a'
        audio = AudioSegment.from_file(file_path, audio_format)
    elif file_path.endswith('.mp4') or file_path.endswith('.MP4') \
            or file_path.endswith('.mov') or file_path.endswith('.MOV'):
        if file_path.endswith('.mov') or file_path.endswith('.MOV'):
            # mov format needs to be converted to mp4 firstly
            file_path = mov_to_mp4(file_path)
            convert_mov = True
            logging.info('convert MOV to mp4: {}'.format(file_path))
        audio_format = 'mp3'
        video_format = 'mp4'
        audio = AudioSegment.from_file(file_path)
        video = editor.VideoFileClip(file_path)
    else:
        raise ValueError('unknown format {}'.format(file_path))

    logging.info('audio ({}), video ({})'.format(audio_format, video_format))
    # numpy array from array.array object
    wave_array_np = np.array(audio.get_array_of_samples())

    # if stereo (channel > 1)
    if audio.channels != 1:
        if audio.channels > 2:
            raise ValueError('audio has more than two channel: {}'.format(audio.channels))
        wave_array_np_left = wave_array_np[0:len(wave_array_np):2]
        wave_array_np_right = wave_array_np[1:len(wave_array_np):2]
        wave_array_np_list = [wave_array_np_left, wave_array_np_right]
    else:
        wave_array_np_list = [wave_array_np]

    # information of audio file
    audio_stats = (audio, wave_array_np_list, audio_format, audio.frame_rate, audio.sample_width, audio.channels)
    video_stats = (video, video_format, convert_mov)
    return audio_stats, video_stats


def write_file(export_file_prefix: str,
               audio,
               audio_format: str,
               video=None,
               video_format: str = None):
    """ Write audio/video to file (format should be same as the input audio file)

     Parameter
    ----------
    export_file_prefix: str
        file prefix for audio/vieo files to be generated
    audio:
        pydub.AudioSegment audio instance
    video:
        moviepy.editor video instance
    audio_format, video_format: str
        audio/video identifier

     Return
    ---------
    generated file path
    """

    def validate_path(__path):
        if os.path.exists(__path):
            os.remove(__path)
        if not os.path.exists(os.path.dirname(__path)):
            os.makedirs(os.path.dirname(__path), exist_ok=True)

    audio_file = '{}.{}'.format(export_file_prefix, audio_format)
    print(audio_file)
    validate_path(audio_file)

    logging.info('save audio to {}'.format(audio_file))
    audio.export(audio_file, format=audio_format)

    if video:
        assert video_format, 'video_format need to be specified'

        video_file_mute = '{}_no_audio.{}'.format(export_file_prefix, video_format)
        validate_path(video_file_mute)
        logging.info('save video to {} without audio'.format(video_file_mute))
        video.write_videofile(video_file_mute)

        video_file = '{}.{}'.format(export_file_prefix, video_format)
        validate_path(video_file)
        logging.info('embed audio to video, and save to {}'.format(video_file))

        combine_audio_video(video_file=video_file_mute, audio_file=audio_file, output_file=video_file)
        return video_file
    else:
        return audio_file
