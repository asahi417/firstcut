import subprocess, os
from moviepy import editor


def combine_audio_video(video_file, audio_file, output_file):
    """ Extract audio data from video

     Parameter
    --------------------
    video_file: str
        path to target video
    audio_file: str
        path to save audio wav file. shoud be end with ~.wav

     Return
    --------------------
    str output message from ffmpeg
    """

    if not (video_file.endswith('.mp4')):
        raise ValueError('unknown video format: %s' % video_file)
    if not (audio_file.endswith('.wav') or audio_file.endswith('.mp3')):
        raise ValueError('unknown audio format: %s' % audio_file)

    if not os.path.exists(video_file):
        raise ValueError('No video file at: %s' % video_file)

    command = "ffmpeg -i %s -i %s -vcodec copy %s" % (video_file, audio_file, output_file)
    try:
        output = subprocess.check_output(
            command, stderr=subprocess.STDOUT, shell=True, timeout=3,
            universal_newlines=True)
    except subprocess.CalledProcessError as exc:
        raise ValueError("Status : FAIL", exc.returncode, exc.output)

    return "Output: \n{}\n".format(output)

PATH = './sample_files/sample_movie_0.mp4'
OUT_PATH_AUDIO = './sample_files/sample_movie_0_io.mp3'
OUT_PATH_VIDEO = './sample_files/sample_movie_0_io.mp4'
OUT_PATH = './sample_files/sample_movie_0_io_combined.mp4'

me_video = editor.VideoFileClip(PATH)
me_audio = editor.AudioFileClip(PATH)

# crop the movie
clips_video = []
clips_audio = []
for s, e in [[1.0, 2.0], [4.0, 5.0], [10.0, 11.0]]:
    clip_video = me_video.subclip(s, e)
    clip_audio = me_audio.subclip(s, e)

    clips_video.append(clip_video)
    clips_audio.append(clip_audio)

me_video_new = editor.concatenate_videoclips(clips_video)
me_audio_new = editor.concatenate_audioclips(clips_audio)

me_audio_new.write_audiofile(OUT_PATH_AUDIO)
me_video_new.write_videofile(OUT_PATH_VIDEO)

combine_audio_video(OUT_PATH_VIDEO, OUT_PATH_AUDIO, OUT_PATH)


# # save audio
# me_audio_new.write_audiofile(OUT_PATH_AUDIO)
# me_video_new.write_videofile(OUT_PATH_VIDEO, audio=OUT_PATH_AUDIO)

# me_video_audio_new = me_video_new.set_audio(me_audio_new.set_duration(me_video_new))
# me_video_audio_new = me_video_new.set_audio(me_audio_new)


