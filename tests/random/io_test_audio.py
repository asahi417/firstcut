import numpy as np
from pydub import AudioSegment

# PATH = './sample_files/sample_3.mp3'
# OUT_PATH = './sample_files/sample_3_io.mp3'

# PATH = './sample_files/sample_1.wav'
# OUT_PATH = './sample_files/sample_1_io.wav'

PATH = './sample_files/sample_movie_0.mp4'
OUT_PATH = './sample_files/sample_movie_0_io.wav'


if PATH.endswith('.mp3'):
    audio_form = 'mp3'
    song = AudioSegment.from_mp3(PATH)
elif PATH.endswith('.wav'):
    audio_form = 'wav'
    song = AudioSegment.from_wav(PATH)
elif PATH.endswith('.mp4'):
    if OUT_PATH.endswith('.wav'):
        audio_form = 'wav'
    elif OUT_PATH.endswith('.mp3'):
        audio_form = 'mp3'
    else:
        raise ValueError('unknown format')
    song = AudioSegment.from_file(PATH, 'mp4')
else:
    raise ValueError('unknown format')

print('\nAudioSegment object')
# what is sample_width? -> http://sites.music.columbia.edu/cmc/MusicAndComputers/chapter2/02_05.php
print(' - frame_rate:', song.frame_rate)
print(' - channels:', song.channels)
print(' - sample_width:', song.sample_width)

print('\nget array.array object from raw sound')
wave_array = song.get_array_of_samples()
print(' - data type:', type(wave_array))
print(' - length:', len(wave_array))
print(' - typecode:', wave_array.typecode)

# ref -> https://stackoverflow.com/questions/35735497/how-to-create-a-pydub-audiosegment-using-an-numpy-array
print('\nconvert to np array')
wave_array_np = np.array(wave_array)
print(' - shape:', wave_array_np.shape)
print(' - dtype:', wave_array_np.dtype)
print(' - dtype itemsize:', wave_array_np.dtype.itemsize)

# form stereo array
if song.channels != 1:
    wave_array_np_left = wave_array_np[0:len(wave_array_np):2]
    wave_array_np_right = wave_array_np[1:len(wave_array_np):2]
    wave_array_np_stereo = np.array([wave_array_np_left, wave_array_np_right])
    print(' - stereo wave:', wave_array_np_stereo.shape)
else:
    wave_array_np_stereo = np.reshape(wave_array_np, [1, -1])

print('\ncut into half size')
wave_array_np_stereo_edit = wave_array_np_stereo[:, :int(wave_array_np_stereo.shape[1]/2)]
print(' - size:', wave_array_np_stereo_edit.shape)

print('\nreturn to serial vector')
wave_array_np_stereo_edit_serial = np.reshape(wave_array_np_stereo_edit.T, [-1])
print(' - size:', wave_array_np_stereo_edit.shape)

# convert into
audio_segment = AudioSegment(
    wave_array_np_stereo_edit_serial.tobytes(),
    # wave_array_org.tobytes(),
    frame_rate=song.frame_rate,
    sample_width=wave_array_np_stereo_edit_serial.dtype.itemsize,
    # sample_width=song.sample_width,
    channels=song.channels
)

# save
audio_segment.export(OUT_PATH, format=audio_form)
