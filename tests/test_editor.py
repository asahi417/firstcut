""" UnitTest editor """
import unittest
import logging
import os

import firstcut

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
# samples from VoxCeleb1 test set
sample_mp3 = './sample_data/vc_1.mp3'
sample_wav = './sample_data/vc_3.wav'
sample_mp4 = './sample_data/vc_4.mp4'
sample_mov = './sample_data/vc_5.mov'


class TestEditor(unittest.TestCase):
    """ Test """

    def test(self):

        for sample in [sample_mp3, sample_wav, sample_mov, sample_mp4]:
            logging.info('process {}'.format(sample))
            editor = firstcut.Editor(sample)
            editor.amplitude_clipping(
                min_interval_sec=0.1,
                cutoff_ratio=0.75
            )
            editor.export('./tests/test_output/test_editor.{}'.format(os.path.basename(sample)))


if __name__ == "__main__":
    unittest.main()
