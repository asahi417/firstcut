""" API job monitoring/numeric check module """
import string
import random
from time import time


def validate_numeric(value, min_val, max_val, is_float=False):
    """ Validate numeric variable (for API parameter validation)

     Parameter
    ---------------
    value: str
        string value
    default: numeric
        default value if given value is None or ""
    min_val: numeric
        numeric value for minimum value
    max_val: numeric
        numeric value for maximum value
    is_float: bool
        use `float` if True else `int`

     Return
    ---------------
    value:
    error_message:
    """
    # value = default if value == '' or value is None else value
    assert type(value) in [str, int, float], 'value should be either str/int/float'
    assert type(min_val) in [int, float] and type(max_val) in [int, float], 'min_val/max_val should be numeric'
    try:
        value = float(value) if is_float else int(value)
    except ValueError:
        return None, 'wrong type'.format(value)

    if value > max_val or value < min_val:
        return None, 'value {} is out of range {} < {}'.format(value, min_val, max_val)

    return value, ''


class Status:
    """ API job monitoring: status_code = {'1': job in progress, '-1': error, '0': job_completed} """

    def __init__(self, keep_log_second: int = 300):
        """ API job monitoring

         Parameter
        ------------
        keep_log_second: int
            maximum time (second) to keep a log
        """
        self.__keep_log_second = keep_log_second
        self.__id_status_dict = dict()

    @staticmethod
    def random_string(string_length: int = 10):
        """ Generate a random string of fixed length """
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for _ in range(string_length))

    @property
    def get_job_ids(self):
        return list(self.__id_status_dict.keys())

    def get_status(self, job_id):
        """ return status: dict(status='status message', status_code='1', unix_timestamp='timestamp of job')"""
        jobs = list(self.__id_status_dict.keys())
        if job_id not in jobs:
            error = {'error_message': 'There are no job of {}. Current jobs are {}'.format(job_id, jobs)}
            return error
        else:
            return self.__id_status_dict[job_id]

    def register_job(self, job_id=None):
        """ Registering job id to status class """
        if job_id is None:
            job_id = self.random_string()
        n = 0
        while True:
            if job_id not in self.__id_status_dict.keys():
                break
            else:
                job_id = self.random_string()
                n += 1
                if n > 10:
                    jobs = list(self.__id_status_dict.keys())
                    raise ValueError('Exceed max size of same job_id: {} in {}'.format(job_id, jobs))

        self.__id_status_dict[job_id] = {
            'status': 'start_job',
            'status_code': '1',
            'unix_timestamp': time(),
            'elapsed_time': 0,
            'progress': 0
        }

        return job_id

    def update(self, job_id, status, refresh: bool = True, progress: float = None):
        self.__update_message(job_id, status, '1', refresh=refresh, progress=progress)

    def complete(self, job_id, **kwargs):
        self.__update_message(job_id, 'completed', '0', refresh=True, progress=100, **kwargs)

    def error(self, job_id, error_message):
        self.__update_message(job_id, error_message, '-1', refresh=True, progress=100)

    def __update_message(self, job_id, status, status_id, refresh: bool = True, progress: float = None, **kwargs):
        if job_id not in self.__id_status_dict.keys():
            raise ValueError('job_id is not registered to status dictionary:  %s' % job_id)
        if refresh:
            self.__id_status_dict[job_id]['status'] = status
            self.__id_status_dict[job_id]['status_code'] = status_id
        else:
            self.__id_status_dict[job_id]['status'] += status
            self.__id_status_dict[job_id]['status_code'] += status_id
        self.__id_status_dict[job_id]['elapsed_time'] = time() - self.__id_status_dict[job_id]['unix_timestamp']
        for k, v in kwargs.items():
            self.__id_status_dict[job_id][k] = v
        if progress is not None:
            self.__id_status_dict[job_id]['progress'] = progress

    def drop(self):
        """ drop job record, which is not in progress status """
        time_now = time()
        delete_ids = []
        for k, v in self.__id_status_dict.items():
            if time_now - v['unix_timestamp'] > self.__keep_log_second:
                if v['status_code'] != '1':  # if job is not in progress
                    delete_ids.append(k)
        if len(delete_ids) != 0:
            for k in delete_ids:
                self.__id_status_dict.pop(k)

