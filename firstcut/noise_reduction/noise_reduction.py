from typing import List

from .bandpass_filter import bandpass_filter
from .nmf import nmf_filter

VALID_METHOD_TYPES = ['bandpass', 'nmf']

__all__ = 'noise_reduction'


def noise_reduction(wave: List,
                    frame_rate: int,
                    method_type: str = 'bandpass',
                    cutoff: List = None,
                    order: int = 6):
        if method_type == 'bandpass':
            single_chanel_wave = wave[0]
            return bandpass_filter(single_chanel_wave,
                                   frame_rate=frame_rate,
                                   cutoff=cutoff,
                                   order=order,
                                   return_filter=return_filter)
        elif method_type == 'nmf':
            ssnmf
        else:
            raise ValueError('unknown `method_type`: {} not in {}'.format(method_type, VALID_METHOD_TYPES))

