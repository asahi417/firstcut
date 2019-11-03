import os
import pyrebase
import subprocess
import logging
from logging.config import dictConfig


__all__ = [
    'combine_audio_video',
    'validate_numeric',
    'create_log',
    'FireBaseConnector',
    'mov_to_mp4'
]

def mov_to_mp4(video_file,
               force: bool=False):
    """ Convert sample.MOV to sample.mp4 by ffmpeg

    `ffmpeg -i sample.MOV -vcodec h264 -acodec mp2 sample.mp4`

     Parameter
    --------------------
    video_file: str
        path to target video
    force: bool
        overwrite if it exists

     Return
    --------------------
    _file: str
        produced file
    _message: str
        message from ffmpeg
    """

    _file, _id = video_file.split('.')
    if not _id in ['mov', 'MOV']:
        raise ValueError('%s is not MOV' % video_file)
    _file += '.mp4'
    command = "ffmpeg -i %s -vcodec h264 -acodec mp2 %s" % (video_file, _file)
    if os.path.exists(_file):
        if force:
            os.system('rm -rf %s' % _file)
        else:
            return _file, ''
    try:
        output = subprocess.check_output(
            command, stderr=subprocess.STDOUT, shell=True, timeout=600,
            universal_newlines=True)
    except subprocess.CalledProcessError as exc:
        if os.path.exists(_file):
            os.system('rm -rf %s' % _file)

        raise ValueError("Status : FAIL", exc.returncode, exc.output)

    return _file, "Output: \n{}\n".format(output)


def combine_audio_video(video_file, audio_file, output_file):
    """ Combine audio data and video by ffmpeg

    `ffmpeg -i sample.mp4 -i sample.mp3 -vcodec copy sample_combined.mp4`

     Parameter
    --------------------
    video_file: str
        path to target video
    audio_file: str
        path to save audio wav file. shoud be end with ~.wav
    output_file
        file name for new combined video file

     Return
    --------------------
    _message: str
        output message from ffmpeg
    """

    if not (video_file.endswith('.mp4')):
        raise ValueError('unknown video format: %s' % video_file)
    if not (audio_file.endswith('.wav') or audio_file.endswith('.mp3')):
        raise ValueError('unknown audio format: %s' % audio_file)

    if not os.path.exists(video_file):
        raise ValueError('No video file at: %s' % video_file)

    if os.path.exists(output_file):
        os.system('rm -rf %s' % output_file)

    command = "ffmpeg -i %s -i %s -vcodec copy %s" % (video_file, audio_file, output_file)
    try:
        output = subprocess.check_output(
            command, stderr=subprocess.STDOUT, shell=True, timeout=600,
            universal_newlines=True)
    except subprocess.CalledProcessError as exc:
        if os.path.exists(output_file):
            os.system('rm -rf %s' % output_file)
        raise ValueError("Status : FAIL", exc.returncode, exc.output)

    return "Output: \n{}\n".format(output)


def validate_numeric(value: str,
                     default,
                     min_val,
                     max_val,
                     is_float=False):
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
    flag: bool
        error flag True if there's any error
    value:
        value for the parameter
    """
    if value == '' or value is None:
        value = default
    try:
        if is_float:
            value = float(value)
        else:
            value = int(value)
    except ValueError:
        return False, f'Param must be a numeric value between "{min_val}" and "{max_val}"'

    if type(max_val) is not float and type(max_val) is not int:
        return False, 'max_val is not numeric: %s' % str(max_val)

    if type(min_val) is not float and type(min_val) is not int:
        return False, 'min_val is not numeric: %s' % str(min_val)

    if value > max_val or value < min_val:
        return False, f'Param must be between {min_val} and {max_val} but {value}'

    return True, value


def create_log():
    """ Logger

    Usage
    -------------------
    logger.info(message)
    logger.error(error)
    """
    logging_config = dict(
        version=1,
        formatters={
            'f': {'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'}
        },
        handlers={
            'h': {'class': 'logging.StreamHandler',
                  'formatter': 'f',
                  'level': logging.DEBUG}
        },
        root={
            'handlers': ['h'],
            'level': logging.DEBUG,
        },
    )
    dictConfig(logging_config)
    logger = logging.getLogger()
    return logger


class FireBaseConnector:
    """ Python client to connect to Fire Base Storage """

    def __init__(self,
                 apiKey,
                 authDomain,
                 databaseURL,
                 storageBucket,
                 gmail,
                 password,
                 serviceAccount):
        """ Python client to connect to Fire Base Storage

         Parameter
        ----------------
        apiKey: Credential
        authDomain: Credential
        databaseURL: Credential
        storageBucket: Credential
        gmail: Credential
        password: Credential
        serviceAccount: Credential
        """
        self.__firebase = pyrebase.initialize_app(
            dict(apiKey=apiKey,
                 authDomain=authDomain,
                 databaseURL=databaseURL,
                 storageBucket=storageBucket,
                 serviceAccount=serviceAccount)
        )
        auth = self.__firebase.auth()
        auth.sign_in_with_email_and_password(gmail, password)
        self.__storage = self.__firebase.storage()

    def get_url(self, file_name: str):
        url = self.__storage.child(file_name).get_url(token=None)
        return url

    def upload(self, file_path: str):
        file_name = os.path.basename(file_path)

        self.__storage.child(file_name).put(file_path)
        url = self.__storage.child(file_name).get_url(token=None)
        return url

    def download(self, file_name, path):
        self.__storage.child(file_name).download(path)

    def remove(self, file_name: str = None):
        if file_name:
            self.__storage.child(file_name).delete(file_name)
            return [file_name]
        else:
            files = self.__storage.list_files()
            removed_list = []
            for file in files:
                self.__storage.child(file.name).delete(file.name)
                removed_list.append(file.name)
            return removed_list

    @property
    def list_files(self):
        return self.__storage.list_files()

