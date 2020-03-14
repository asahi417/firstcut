""" API job monitoring """

import string
import random
from time import time


class Status:
    """ status keeper: status_code = {'1': job in progress, '-1': error, '0': job_completed} """

    def __init__(self, keep_log_second: int=300):
        self.__keep_log_second = keep_log_second
        self.__id_status_dict = dict()

    @staticmethod
    def random_string(string_length=10):
        """Generate a random string of fixed length """
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(string_length))

    @property
    def get_job_ids(self):
        return list(self.__id_status_dict.keys())

    def get_status(self, job_id):
        """ return status: dict(status='status message', status_code='1', unix_timestamp='timestamp of job')"""
        if job_id not in self.__id_status_dict.keys():
            error = dict(error_message=
                         'There are no job of %s. Current jobs are %s' % (job_id, list(self.__id_status_dict.keys())))
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
                    raise ValueError('Exceed max size of same job_id: %s in %s' %
                                     (job_id, list(self.__id_status_dict.keys())))

        self.__id_status_dict[job_id] = dict(
            status='start_job', status_code='1', unix_timestamp=time(), elapsed_time=0, progress=0)
        return job_id

    def update(self, job_id, status, refresh=True, progress: float = None):
        self.__update_message(job_id, status, '1', refresh=refresh, progress=progress)

    def complete(self, job_id, url):
        self.__update_message(job_id, 'completed', '0', url=url, refresh=True, progress=100)

    def error(self, job_id, error_message):
        self.__update_message(job_id, error_message, '-1', refresh=True, progress=100)

    def __update_message(self, job_id, status, status_id, url='', refresh=True, progress: float = None):
        if job_id not in self.__id_status_dict.keys():
            raise ValueError('job_id is not registered to status dictionary:  %s' % job_id)
        if refresh:
            self.__id_status_dict[job_id]['status'] = status
            self.__id_status_dict[job_id]['status_code'] = status_id
        else:
            self.__id_status_dict[job_id]['status'] += status
            self.__id_status_dict[job_id]['status_code'] += status_id
        self.__id_status_dict[job_id]['elapsed_time'] = time() - self.__id_status_dict[job_id]['unix_timestamp']
        self.__id_status_dict[job_id]['url'] = url
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

