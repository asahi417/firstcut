# """ Frequency filter
#
# # lowpass filter
# >>>
#
# """
#
#
# from scipy.signal import butter, lfilter, freqz
# import matplotlib.pyplot as plt
#
#
# def butter_lowpass(cutoff, fs, order=5):
#     """ coefficients for filter """
#     nyq = 0.5 * fs
#     normal_cutoff = cutoff / nyq
#     b, a = butter(order, normal_cutoff, btype='low', analog=False)
#     return b, a
#
#
# def butter_lowpass_filter(data, cutoff, fs, order=5):
#     """
#      Parameter
#     -----------------
#     data: 1-dimension numpy array
#         signal to edit
#     cutoff: int
#         cutoff frequency
#     fs: int
#         frequency of given signal
#     order: int
#         order for filtering function
#     :return:
#     """
#     b, a = butter_lowpass(cutoff, fs, order=order)
#     y = lfilter(b, a, data)
#     return y
