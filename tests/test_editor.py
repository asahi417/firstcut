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
sample_noise = './sample_data/vc_6.wav'


class TestEditor(unittest.TestCase):
    """ Test """

    def test_vis(self):
        basename = os.path.basename(sample_wav).split('.')[0]
        editor = firstcut.Editor(sample_wav)
        editor.plot(figure_type='signal',
                    path_to_save='./tests/test_output/test_editor.{}.png'.format(basename))

    def test_noise_and_cut(self):
        basename = os.path.basename(sample_noise).split('.')[0]

        editor = firstcut.Editor(sample_noise)
        editor.amplitude_clipping()
        editor.export('./tests/test_output/test_editor.{}'.format(basename))

        editor = firstcut.Editor(sample_noise)
        editor.noise_reduction()
        editor.amplitude_clipping()
        editor.export('./tests/test_output/test_editor.{}.denoised'.format(basename))

    def test(self):

        for sample in [sample_mp3, sample_wav, sample_mov, sample_mp4]:
            basename = os.path.basename(sample).split('.')[0]
            logging.info('process {}'.format(sample))
            editor = firstcut.Editor(sample)
            editor.amplitude_clipping(
                min_interval_sec=0.1,
                cutoff_ratio=0.75
            )
            editor.export('./tests/test_output/test_editor.{}'.format(basename))


if __name__ == "__main__":
    unittest.main()
