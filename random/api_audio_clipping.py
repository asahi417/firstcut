"""
Video/Audio clipping API
"""

import nitro_editor
from threading import Thread
import traceback
import os
import urllib.request
from time import time
from flask import Flask, request, jsonify
# from werkzeug.exceptions import BadRequest

app = Flask(__name__)

PORT = int(os.getenv("PORT", "7003"))
ROOT_DIR = os.path.expanduser("~")
MIN_INTERVAL_SEC = float(os.getenv("MIN_INTERVAL_SEC", "0.2"))
MIN_AMPLITUDE = float(os.getenv("MIN_AMPLITUDE", "0.1"))
TMP_DOWNLOAD_FILE = os.path.join(ROOT_DIR, 'tmp_download')


class Status:
    def __init__(self, initial_status, initial_status_code=0):
        self.__initial_status = initial_status
        self.__current_status = initial_status
        self.__initial_status_code = initial_status_code
        self.__current_status_code = initial_status_code

    @property
    def now(self):
        return str(self.__current_status), int(self.__current_status_code)

    def set_status(self, status, status_code):
        self.__current_status = status
        self.__current_status_code = status_code

    def close(self):
        self.__current_status = self.__initial_status
        self.__current_status_code = self.__initial_status_code


def main():
    job_status = Status('no_jobs', 0)
    logger = nitro_editor.util.create_log()

    def process(path_to_file,
                path_to_save,
                min_interval_sec,
                min_amplitude,
                tmp_download):

        job_status.set_status('processing', 1)
        try:
            if tmp_download.endswith('wav'):
                editor = nitro_editor.audio.Editor(path_to_file)
            elif tmp_download.endswith('mp4'):
                editor = nitro_editor.video.Editor(path_to_file)
            else:
                raise ValueError('unknown format: %s' % path_to_file)

            editor.amplitude_clipping(min_amplitude=min_amplitude, min_interval_sec=min_interval_sec)
            editor.write(path_to_save)
            job_status.close()

            if os.path.exists(tmp_download):
                logger.info('delete downloaded file: %s' % tmp_download)
                os.system('rm -rf %s' % tmp_download)

        except Exception:
            msg = traceback.format_exc()
            logger.error(msg)
            job_status.set_status(
                dict(error_msg=msg,
                     parameter=dict(path_to_audio=path_to_file,
                                    path_to_save=path_to_save,
                                    min_interval_sec=min_interval_sec,
                                    min_amplitude=min_amplitude)),
                -1
            )

    @app.route("/video_clipping", methods=["POST"])
    def video_clipping_endpoint():
        logger.info('video clipping: new request')

        if request.method != "POST":
            return jsonify(status="ERROR: Bad Method `%s`. Only POST method is allowed." % request.method)

        if request.headers.get("Content-Type") != 'application/json':
            return jsonify(status="ERROR: Bad Content-Type `%s`. Only application/json Content-Type is allowed."
                                  % request.headers)

        post_body = request.get_json()
        tmp_download_file = TMP_DOWNLOAD_FILE + '.mp4'

        def required_param_validate(name):
            tmp = post_body.get(name, "")
            is_error = False
            if tmp == "":
                is_error = True
                msg = "Error: Parameter `%s` is required." % name
                return msg, is_error
            if tmp.startswith('http'):
                logger.info('download file from %s' % tmp)
                urllib.request.urlretrieve(tmp, tmp_download_file)

                start = time()
                while True:
                    if os.path.exists(tmp_download_file):
                        break
                    if time() - start > 30:
                        is_error = True
                        msg = 'ERROR: Runtime error, can not download file: %s ' % tmp_download_file
                        return msg, is_error
                tmp = tmp_download_file
                return tmp, is_error
            logger.info(' - %s: %s' % (name, str(tmp)))
            return tmp, is_error

        def param_validate(name, default, min_val, max_val, data_type=float):
            param_value = post_body.get(name, default)
            is_error = False
            if param_value is None:
                return param_value

            try:
                numeric_val = data_type(param_value)
            except ValueError:
                msg = f'Param "{name}" must be a numeric value between "{min_val}" and "{max_val}"'
                is_error = True
                return msg, is_error

            if numeric_val > max_val or numeric_val < min_val:
                msg = f'Param "{name}" must be between {min_val} and {max_val}'
                is_error = True
                return msg, is_error

            logger.info(' - %s: %s' % (name, str(numeric_val)))
            return numeric_val, is_error

        logger.info('parameters')

        output, _is_error = required_param_validate('file_path')
        if _is_error:
            return jsonify(status='ERROR: %s' % output)
        else:
            file_path = output

        output, _is_error = required_param_validate('output_path')
        if _is_error:
            return jsonify(status='ERROR: %s' % output)
        else:
            output_path = output

        output, _is_error = param_validate('min_interval_sec', MIN_INTERVAL_SEC, 0.0, 10000, float)
        if _is_error:
            return jsonify(status='ERROR: %s' % output)
        else:
            min_interval_sec = output

        output, _is_error = param_validate('min_amplitude', MIN_AMPLITUDE, 0.0, 100, float)
        if _is_error:
            return jsonify(status='ERROR: %s' % output)
        else:
            min_amplitude = output

        logger.info('start process')
        thread = Thread(target=process,
                        args=[file_path, output_path, min_interval_sec, min_amplitude, tmp_download_file])
        thread.start()
        return jsonify(status='process started')

    @app.route("/audio_clipping", methods=["POST"])
    def audio_clipping_endpoint():
        logger.info('audio clipping: new request')

        if request.method != "POST":
            return jsonify(status="ERROR: Bad Method `%s`. Only POST method is allowed." % request.method)

        if request.headers.get("Content-Type") != 'application/json':
            # return BadRequest("ERROR: Only application/json Content-Type is allowed.")
            return jsonify(status="ERROR: Bad Content-Type `%s`. Only application/json Content-Type is allowed."
                                  % request.headers)

        post_body = request.get_json()
        tmp_download_file = TMP_DOWNLOAD_FILE + '.wav'

        def required_param_validate(name):
            tmp = post_body.get(name, "")
            is_error = False
            if tmp == "":
                is_error = True
                msg = "Error: Parameter `%s` is required." % name
                return msg, is_error
            if tmp.startswith('http'):
                logger.info('download file from %s' % tmp)
                urllib.request.urlretrieve(tmp, tmp_download_file)

                start = time()
                while True:
                    if os.path.exists(tmp_download_file):
                        break
                    if time() - start > 30:
                        is_error = True
                        msg = 'ERROR: Runtime error, can not download file: %s ' % tmp_download_file
                        return msg, is_error
                tmp = tmp_download_file
                return tmp, is_error
            logger.info(' - %s: %s' % (name, str(tmp)))
            return tmp, is_error

        def param_validate(name, default, min_val, max_val, data_type=float):
            param_value = post_body.get(name, default)
            is_error = False
            if param_value is None:
                return param_value

            try:
                numeric_val = data_type(param_value)
            except ValueError:
                msg = f'Param "{name}" must be a numeric value between "{min_val}" and "{max_val}"'
                is_error = True
                return msg, is_error

            if numeric_val > max_val or numeric_val < min_val:
                msg = f'Param "{name}" must be between {min_val} and {max_val}'
                is_error = True
                return msg, is_error

            logger.info(' - %s: %s' % (name, str(numeric_val)))
            return numeric_val, is_error

        logger.info('parameters')

        output, _is_error = required_param_validate('file_path')
        if _is_error:
            return jsonify(status='ERROR: %s' % output)
        else:
            file_path = output

        output, _is_error = required_param_validate('output_path')
        if _is_error:
            return jsonify(status='ERROR: %s' % output)
        else:
            output_path = output

        output, _is_error = param_validate('min_interval_sec', MIN_INTERVAL_SEC, 0.0, 10000, float)
        if _is_error:
            return jsonify(status='ERROR: %s' % output)
        else:
            min_interval_sec = output

        output, _is_error = param_validate('min_amplitude', MIN_AMPLITUDE, 0.0, 100, float)
        if _is_error:
            return jsonify(status='ERROR: %s' % output)
        else:
            min_amplitude = output

        logger.info('start process')
        thread = Thread(target=process, args=[file_path, output_path, min_interval_sec, min_amplitude, tmp_download_file])
        thread.start()
        return jsonify(status='process started')

    @app.route("/job_status")
    def job_status_endpoint():
        """ job_status to check status of current job """
        status, status_code = job_status.now
        return jsonify(status=status, status_code=status_code)

    app.run(host="0.0.0.0", port=PORT, debug=False)


if __name__ == '__main__':
    main()
