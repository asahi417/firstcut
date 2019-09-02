from moviepy import editor

PATH = './sample_files/sample_movie_0.mp4'
OUT_PATH_AUDIO = './sample_files/sample_movie_0_io.mp4'
OUT_PATH_VIDEO = './sample_files/sample_movie_0_io.mp4'

me_video = editor.VideoFileClip(PATH)
me_audio = editor.AudioFileClip(PATH)

clips_video = []
clips_audio = []
for s, e in [[0.0, 2.0], [4.0, 5.0], [10.0, 12.0]]:
    clip_video = me_video.subclip(s, e)
    clip_audio = me_audio.subclip(s, e)

    clips_video.append(clip_video)
    clips_audio.append(clip_audio)

me_audio_new = editor.concatenate_audioclips(clips_audio)
me_audio_new.set_duration(me_audio_new)

me_video_new = editor.concatenate_videoclips(clips_video)

me_video_audio_new = me_video_new.set_audio(me_audio_new)
me_video_audio_new.write_videofile(OUT_PATH)

