import numpy as np
import librosa

import nmf

def SSNMF(y_o, y_n):
    # y_n: Noise Signal
    # y_o: Original Signal
    BasisNoiseNum = 20
    BasisNum = 20

    # training
    Y_n = librosa.stft(y_n)
    Out = nmf.NMF(np.abs(Y_n), R=BasisNoiseNum)
    H_n = Out[0]

    # separation
    Y_o = librosa.stft(y_o)
    Out = nmf.NMF(np.abs(Y_o), R=BasisNoiseNum+BasisNum, basis_H=H_n)

    # Wiener filter 
    Y_est = np.dot(Out[0], Out[1])
    Y_target = np.dot(Out[0][0:,BasisNoiseNum:BasisNoiseNum+BasisNum], \
                Out[1][BasisNoiseNum:BasisNoiseNum+BasisNum,0:])
    eps = np.spacing(1)

    Y_sep = np.abs(Y_o) * (Y_target / (Y_est + eps))
    Y_phase = np.cos(np.angle(Y_o) + 1j * np.sin(np.angle(Y_o)))
    y_out = librosa.istft(Y_sep * Y_phase)

    return y_out

y, sr = librosa.load('sample_2.wav')
y_n = y[0:8000]
y_o, sr = librosa.load('sample_2.wav')

y_out = SSNMF(y_o, y_n)

librosa.output.write_wav("out.wav", y_out, sr)