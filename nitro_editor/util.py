import os
import logging
import pyrebase


def validate_numeric(value: str, default, min_val, max_val, is_float=False):
    """ Validate numeric variable (for API parameter validation)

    :param value: string value
    :param default: default value if given value is None or ""
    :param min_val: numeric value
    :param max_val: numeric value
    :param is_float: use `float` if True else `int`
    :return: (flag, value), if flag is False, there should be error and value is error message

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


def create_log(out_file_path=None):
    """ Logging
        If `out_file_path` is None, only show in terminal
        or else save log file in `out_file_path`

    Usage
    -------------------
    logger.info(message)
    logger.error(error)
    """

    # handler to record log to a log file
    if out_file_path is not None:
        if os.path.exists(out_file_path):
            os.remove(out_file_path)
        logger = logging.getLogger(out_file_path)

        if len(logger.handlers) > 1:  # if there are already handler, return it
            return logger
        else:
            logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter("H1, %(asctime)s %(levelname)8s %(message)s")

            handler = logging.FileHandler(out_file_path)
            handler.setFormatter(formatter)
            logger.addHandler(handler)

            logger_stream = logging.getLogger()
            # check if some stream handlers are already
            if len(logger_stream.handlers) > 0:
                return logger
            else:
                handler = logging.StreamHandler()
                handler.setFormatter(formatter)
                logger.addHandler(handler)

                return logger
    else:
        # handler to output
        handler = logging.StreamHandler()
        logger = logging.getLogger()

        if len(logger.handlers) > 0:  # if there are already handler, return it
            return logger
        else:  # in case of no, make new output handler
            logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter("H1, %(asctime)s %(levelname)8s %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            return logger


class FireBaseConnector:

    def __init__(self,
                 apiKey,
                 authDomain,
                 databaseURL,
                 storageBucket,
                 gmail,
                 password,
                 serviceAccount):
        # initialize
        self.__firebase = pyrebase.initialize_app(dict(
            apiKey=apiKey,
            authDomain=authDomain,
            databaseURL=databaseURL,
            storageBucket=storageBucket,
            serviceAccount=serviceAccount
        ))
        # authentication
        auth = self.__firebase.auth()
        auth.sign_in_with_email_and_password(gmail, password)
        self.__storage = self.__firebase.storage()

    def upload(self, file_path: str):
        file_name = os.path.basename(file_path)

        # img_url = self.__storage.child(file_name).put(file_path)
        # print(img_url)
        # url = self.__storage.child(file_name).get_url(img_url['downloadTokens'])
        # print(url)

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

