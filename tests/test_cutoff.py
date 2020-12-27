""" UnitTest cutoff method """
import os
import unittest
import logging

import firstcut

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
# samples from VoxCeleb1 test set
sample_mp3 = './sample_data/vc_1.mp3'
sample_wav = './sample_data/vc_3.wav'


class TestCut(unittest.TestCase):
    """ Test """

    def test(self):
        for sample in [sample_mp3, sample_wav]:
            audio_stats, video_stats = firstcut.load_file(sample)
            (audio, wave_array_np_list, audio_format, frame_rate, sample_width, channels) = audio_stats
            # (video, video_format, convert_mov) = video_stats

            p = 0.99
            c = firstcut.get_cutoff_amplitude(wave_array_np_list[0], cutoff_ratio=p)
            logging.info('get_cutoff_amplitude: {} ({} ratio)'.format(c, p))
            firstcut.visualize_cutoff_amplitude(
                c, wave_array_np_list[0],
                frame_rate=frame_rate,
                path_to_save='./tests/test_output/test_cutoff.{}.png'.format(os.path.basename(sample)))


if __name__ == "__main__":
    unittest.main()
