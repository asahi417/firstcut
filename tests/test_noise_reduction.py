""" UnitTest noise reduction """
import unittest
import logging
import os

import firstcut

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
# samples from VoxCeleb1 test set
sample_mp3 = './sample_data/vc_1.mp3'
sample_wav = './sample_data/vc_6.wav'


class TestNR(unittest.TestCase):
    """ Test """

    def test(self):

        logging.info('process {}'.format(sample_wav))
        basename = os.path.basename(sample_wav).split('.')[0]
        editor = firstcut.Editor(sample_wav)
        editor.noise_reduction('nmf')
        editor.plot(
            figure_type='noise_reduction',
            path_to_save='./tests/test_output/test_noise_reduction.{}.png'.format(basename))
        editor.export('./tests/test_output/test_noise_reduction.{}.wav'.format(os.path.basename(basename)))


if __name__ == "__main__":
    unittest.main()
