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
        audio_stats, video_stats = firstcut.load_file(sample_mp3)
        (audio, wave_array_np_list, audio_format, frame_rate, sample_width, channels) = audio_stats

        p = 0.99
        c = firstcut.get_cutoff_amplitude(wave_array_np_list[0], cutoff_ratio=p)
        logging.info('get_cutoff_amplitude: {} ({} ratio)'.format(c, p))
        basename = os.path.basename(sample_mp3).split('.')[0]
        firstcut.visualize_cutoff_amplitude(
            c, wave_array_np_list[0],
            frame_rate=frame_rate,
            path_to_save='./tests/test_output/test_cutoff.{}.png'.format(basename))

    def test_editor(self):
        basename = os.path.basename(sample_wav).split('.')[0]
        editor = firstcut.Editor(sample_wav)
        editor.amplitude_clipping(min_interval_sec=0.12, cutoff_ratio=0.99)
        editor.plot(
            figure_type='amplitude_clipping',
            path_to_save='./tests/test_output/test_cutoff.{}.png'.format(basename))


if __name__ == "__main__":
    unittest.main()
