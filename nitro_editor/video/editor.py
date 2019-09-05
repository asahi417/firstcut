# from moviepy import editor
# import os
# import subprocess
# from .. import audio
# from ..util import create_log
#
# VALID_FORMAT = ['mp4']
# LOG = create_log()
#
#
# # def clean_file(_file):
# #     if os.path.exists(_file):
# #         os.remove(_file)
#
#
# # def extract_audio_from_video(video_file, audio_file):
# #     """ Extract audio data from video
# #
# #      Parameter
# #     --------------------
# #     video_file: str
# #         path to target video
# #     audio_file: str
# #         path to save audio wav file. shoud be end with ~.wav
# #
# #      Return
# #     --------------------
# #     str output message from ffmpeg
# #     """
# #
# #     assert video_file.endswith('.mp4')
# #     assert audio_file.endswith('.wav')
# #
# #     if not os.path.exists(video_file):
# #         raise ValueError('No video file at: %s' % video_file)
# #     command = "ffmpeg -i %s -ab 160k -ac 2 -ar 44100 -vn %s" % (video_file, audio_file)
# #
# #     try:
# #         output = subprocess.check_output(
# #             command, stderr=subprocess.STDOUT, shell=True, timeout=3,
# #             universal_newlines=True)
# #     except subprocess.CalledProcessError as exc:
# #         raise ValueError("Status : FAIL", exc.returncode, exc.output)
# #
# #     return "Output: \n{}\n".format(output)
#
#
# def combine_audio_video(video_file, audio_file, output_file):
#     """ Extract audio data from video
#
#      Parameter
#     --------------------
#     video_file: str
#         path to target video
#     audio_file: str
#         path to save audio wav file. shoud be end with ~.wav
#
#      Return
#     --------------------
#     str output message from ffmpeg
#     """
#
#     if not (video_file.endswith('.mp4')):
#         raise ValueError('unknown video format: %s' % video_file)
#     if not (audio_file.endswith('.wav') or audio_file.endswith('.mp3')):
#         raise ValueError('unknown audio format: %s' % audio_file)
#
#     if not os.path.exists(video_file):
#         raise ValueError('No video file at: %s' % video_file)
#
#     command = "ffmpeg -i %s -i %s -vcodec copy %s" % (video_file, audio_file, output_file)
#     try:
#         output = subprocess.check_output(
#             command, stderr=subprocess.STDOUT, shell=True, timeout=3,
#             universal_newlines=True)
#     except subprocess.CalledProcessError as exc:
#         raise ValueError("Status : FAIL", exc.returncode, exc.output)
#
#     LOG.debug("Output: \n{}\n".format(output))
#
# class VideoEditor:
#
#     @property
#     def video(self):
#         return self.__video
#
#     @property
#     def audio(self):
#         return self.__audio_editor.audio
#
#     def __init__(self, file_path):
#         assert file_path.endswith('.mp4')
#         if not os.path.exists(file_path):
#             raise ValueError('No file at: %s' % file_path)
#
#         # load audio file
#         self.__tmp_audio_path = os.path.join(os.path.dirname(file_path), 'tmp.wav')
#         self.__tmp_video_path = os.path.join(os.path.dirname(file_path), 'tmp.mp4')
#
#         clean_file(self.__tmp_audio_path)
#         extract_audio_from_video(file_path, self.__tmp_audio_path)
#         self.__audio_editor = AudioEditor(self.__tmp_audio_path)
#         clean_file(self.__tmp_audio_path)
#
#         # load video
#         self.__video = editor.VideoFileClip(file_path)
#
#     def amplitude_clipping(self,
#                            min_amplitude: float,
#                            min_interval_sec: int):
#         """ Amplitude-based truncation. In given audio signal, where every sampling point has amplitude
#             less than `min_amplitude` and the length is greater than `min_interval`, will be removed.
#
#
#          Parameter
#         ---------------
#         min_amplitude: float
#             minimum amplitude to cutoff
#         min_interval_sec: int
#             minimum interval of cutoff (sec)
#         """
#
#         # edit audio signal
#         self.__audio_editor.amplitude_clipping(min_amplitude, min_interval_sec)
#
#         # edit video data
#         sub_videos = []
#         # i = 0
#         for s, e in self.__audio_editor.keep_part_sec:
#             # i += e - s
#             # print(i)
#             sub_videos.append(self.__video.subclip(s, e))
#
#         # print('full', self.__audio_editor.length_sec)
#         # print('keep', self.__audio_editor.keep_part_sec)
#
#         self.__video = editor.concatenate_videoclips(sub_videos)
#
#     def write(self, _file):
#
#         if os.path.exists(_file):
#             os.remove(_file)
#         elif not os.path.exists(os.path.dirname(_file)):
#                 os.makedirs(os.path.dirname(_file), exist_ok=True)
#
#         clean_file(self.__tmp_audio_path)
#         self.__audio_editor.write(self.__tmp_audio_path)
#
#         clean_file(self.__tmp_video_path)
#         self.__video.write_videofile(self.__tmp_video_path)
#
#         combine_wav_mp4(mp4_file=self.__tmp_video_path, wav_file=self.__tmp_audio_path, output_file=_file)
#
#         clean_file(self.__tmp_audio_path)
#         clean_file(self.__tmp_video_path)