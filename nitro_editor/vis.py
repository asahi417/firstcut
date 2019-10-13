# """ visualization script """
# import numpy as np
# from matplotlib import pyplot as plt
#
# __all__ = ['vis_frequency']
#
# def vis_frequency(wave_data,
#                   freq,
#                   path_to_save: str=None):
#
#     n = len(wave_data) # length of the signal
#     k = np.arange(n)
#     t = n/freq
#     frq = k/t # two sides frequency range
#     frq = frq[range(int(n/2))] # one side frequency range
#
#     data_freq = np.fft.fft(wave_data)/n # fft computing and normalization
#     data_freq = data_freq[range(int(n/2))]
#
#     plt.figure(figsize=(6, 4))
#     plt.title('Frequency spectrum (%0.1f Hz)' % freq)
#
#     plt.plot(frq, abs(data_freq)) # plotting the spectrum
#     plt.grid()
#     plt.xlabel("Freq (Hz)")
#     plt.ylabel("|Y(freq)|")
#     plt.xlim([0, frq.max()])
#     plt.ylim([0, abs(data_freq).max() + 5])
#
#
#     if path_to_save:
#         plt.savefig(path_to_save)
