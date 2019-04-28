import audio_editor
from threading import Thread
import traceback
import os

from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest

app = Flask(__name__)

PORT = int(os.getenv("PORT", "7001"))
ROOT_DIR = os.getenv("ROOT_DIR", os.path.expanduser("~"))
MIN_INTERVAL_SEC = float(os.getenv("PORT", "0.2"))
MIN_AMPLITUDE = float(os.getenv("MIN_AMPLITUDE", "0.1"))


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
    logger = audio_editor.create_log()

    def process(path_to_audio,
                path_to_save,
                file_format,
                min_interval_sec,
                min_amplitude):

        job_status.set_status('processing', 1)
        try:
            # load wav file
            print(path_to_audio)
            audio_signal, freq = audio_editor.load_audio(path_to_audio,
                                                         file_format=file_format)
            # convert from second to sampling length
            min_interval = int(min_interval_sec * freq)
            # truncate audio
            audio_signal_edit = audio_editor.truncation_function.amplitude_filter(
                audio_signal,
                min_amplitude=min_amplitude,
                min_interval=min_interval)
            # write audio file
            if not os.path.exists(os.path.dirname(path_to_save)):
                os.makedirs(os.path.dirname(path_to_save), exist_ok=True)
            audio_editor.write_audio(path_to_save, audio_signal_edit, freq, file_format=file_format)
            job_status.close()
        except Exception:
            msg = traceback.format_exc()
            logger.error(msg)
            job_status.set_status(
                dict(error_msg=msg,
                     parameter=dict(path_to_audio=path_to_audio,
                                    path_to_save=path_to_save,
                                    file_format=file_format,
                                    min_interval_sec=min_interval_sec,
                                    min_amplitude=min_amplitude)),
                -1
            )

    @app.route("/wav_truncation", methods=["POST"])
    def wav_truncation_endpoint():
        logger.info('new request')

        if request.method != "POST":
            BadRequest("Only POST method is allowed.")

        post_body = request.get_json()

        def required_param_validate(name):
            tmp = post_body.get(name, "")
            if tmp == "":
                return BadRequest("Error: Parameter `%s` is required." % name)
            if not tmp.endswith(".wav"):
                return BadRequest("Error: `file_path` have to be `wav` format:"
                                  "%s is not wav file." % tmp)
            logger.info(' - %s: %s' % (name, str(tmp)))
            return tmp

        def param_validate(name, default, min_val, max_val, data_type=float):
            param_value = post_body.get(name, default)
            if param_value is None:
                return param_value

            try:
                numeric_val = data_type(param_value)
            except ValueError:
                return BadRequest(
                    f'Param "{name}" must be a numeric value '
                    f"between {min_val} and {max_val}"
                )
            if numeric_val > max_val or numeric_val < min_val:
                return BadRequest(f'Param "{name}" must be between {min_val} and {max_val}')

            logger.info(' - %s: %s' % (name, str(numeric_val)))
            return numeric_val

        logger.info('parameters')
        file_path = os.path.join(ROOT_DIR, required_param_validate('file_path'))
        output_path = os.path.join(ROOT_DIR, required_param_validate('output_path'))
        min_interval_sec = param_validate('min_interval_sec', MIN_INTERVAL_SEC, 0.0, 10000, float)
        min_amplitude = param_validate('min_amplitude', MIN_AMPLITUDE, 0.0, 100, float)

        logger.info('start process')
        thread = Thread(target=process, args=[file_path, output_path, 'wav', min_interval_sec, min_amplitude])
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
