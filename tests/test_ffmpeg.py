""" UnitTest """
import unittest
import logging
import shutil
import os

from firstcut import ffmpeg

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
# samples from VoxCeleb1 test set
sample_mp3 = './sample_data/vc_1.mp3'
sample_wav = './sample_data/vc_3.wav'
sample_mp4 = './sample_data/vc_4.mp4'
sample_mov = './sample_data/vc_5.mov'


class TestFFMPEG(unittest.TestCase):
    """ Test """

    def test(self):
        """ convert mov to mp4 """
        audio_stats, video_stats = ffmpeg.load_file(sample_mov)
        (audio, wave_array_np_list, audio_format, audio.frame_rate, audio.sample_width, audio.channels) = audio_stats
        (video, video_format, convert_mov) = video_stats
        assert convert_mov
        export_file = ffmpeg.write_file(export_file_prefix='./sample_data/vc_5_test',
                                        audio=audio, video=video, audio_format=audio_format, video_format=video_format)
        assert os.path.exists(export_file)
        os.remove(export_file)
        os.remove('./sample_data/vc_5_test.mp3')
        os.remove('./sample_data/vc_5_test_no_audio.mp4')

    def test_load_file(self):
        """ load_file """
        ffmpeg.load_file(sample_mp3)
        ffmpeg.load_file(sample_wav)
        ffmpeg.load_file(sample_mp4)
        ffmpeg.load_file(sample_mov)

    def test_mov_to_mp4(self):
        """ mov_to_mp4 """
        export_file = ffmpeg.mov_to_mp4(sample_mov)
        logging.info(export_file)
        assert os.path.exists(export_file)
        os.remove(export_file)


if __name__ == "__main__":
    unittest.main()