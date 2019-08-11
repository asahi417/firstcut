""" Video/Audio clipping API """

import nitro_editor
from threading import Thread
import traceback
import os
from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest, InternalServerError

app = Flask(__name__)

ROOT_DIR = os.path.expanduser("~")

PORT = int(os.getenv("PORT", "8008"))
MIN_INTERVAL_SEC = float(os.getenv("MIN_INTERVAL_SEC", "0.2"))
MIN_AMPLITUDE = float(os.getenv("MIN_AMPLITUDE", "0.1"))
KEEP_LOG_SEC = int(os.getenv('KEEP_LOG_SEC', '180'))

FIREBASE_SERVICE_ACOUNT = os.getenv('FIREBASE_SERVICE_ACOUNT', None)
FIREBASE_APIKEY = os.getenv('FIREBASE_APIKEY', None)
FIREBASE_AUTHDOMAIN = os.getenv('FIREBASE_AUTHDOMAIN', None)
FIREBASE_DATABASEURL = os.getenv('FIREBASE_DATABASEURL', None)
FIREBASE_STORAGEBUCKET = os.getenv('FIREBASE_STORAGEBUCKET', None)

FIREBASE_GMAIL = os.getenv('FIREBASE_GMAIL', None)
FIREBASE_PASSWORD = os.getenv('FIREBASE_PASSWORD', None)


def main():
    job_status_instance = nitro_editor.job_status.Status(keep_log_second=KEEP_LOG_SEC)
    logger = nitro_editor.util.create_log()
    firebase = nitro_editor.util.FireBaseConnector(
        apiKey=FIREBASE_APIKEY,
        authDomain=FIREBASE_AUTHDOMAIN,
        databaseURL=FIREBASE_DATABASEURL,
        storageBucket=FIREBASE_STORAGEBUCKET,
        serviceAccount=FIREBASE_SERVICE_ACOUNT,
        gmail=FIREBASE_GMAIL,
        password=FIREBASE_PASSWORD
    )
    # directory where audio/video files are temporarily stored
    tmp_storage_audio = os.path.join(ROOT_DIR, 'nitro_editor_data', 'tmp_audio')
    if not os.path.exists(tmp_storage_audio):
        os.makedirs(tmp_storage_audio, exist_ok=True)
    tmp_storage_video = os.path.join(ROOT_DIR, 'nitro_editor_data', 'tmp_video')
    if not os.path.exists(tmp_storage_video):
        os.makedirs(tmp_storage_video, exist_ok=True)

    def process(job_id,
                file_name,
                min_interval_sec,
                min_amplitude):
        try:

            # download file from firebase
            job_status_instance.update(job_id=job_id, status=' - downloading data from firebase')
            if file_name.endswith('.wav'):
                path_file = os.path.join(tmp_storage_audio, job_id + '_raw.wav')
                path_save = os.path.join(tmp_storage_audio, job_id + '_processed.wav')
            elif file_name.endswith('.mp4'):
                path_file = os.path.join(tmp_storage_video, job_id + '_raw.mp4')
                path_save = os.path.join(tmp_storage_video, job_id + '_processed.mp4')
            else:
                raise ValueError('unknown file format: %s' % file_name)
            firebase.download(file_name=file_name, path=path_file)

            # edit
            job_status_instance.update(job_id=job_id, status=' - start processing')
            editor = nitro_editor.audio.Editor(path_file)
            editor.amplitude_clipping(min_amplitude=min_amplitude, min_interval_sec=min_interval_sec)
            editor.write(path_save)

            # upload
            job_status_instance.update(job_id=job_id, status=' - uploading processed data')
            url = firebase.upload(file_path=path_save)

            # clean local storage
            os.system('rm -rf %s' % path_file)
            os.system('rm -rf %s' % path_save)

            # update job status
            job_status_instance.complete(job_id=job_id, url=url)

        except Exception:
            msg = traceback.format_exc()
            logger.error('job_id `%s` raises InternalServerError\n %s' % (job_id, msg))
            job_status_instance.error(job_id=job_id, error_message=msg)

    @app.route("/audio_clip", methods=["POST"])
    def audio_clip():
        """ Audio clip API endpoint

        - Description: POST API to truncate wav audio file.
        - Endpoint: `audio_clip`
        - Parameters:

        | Parameter name                            | Default              | Description
        | ----------------------------------------- | -------------------- | -------------------------------
        | **file_name**<br />_(\* required)_        |  -                   | file name in firebase project
        | **min_interval_sec**                      | **MIN_INTERVAL_SEC** | minimum interval of part to exclude (sec)
        | **min_amplitude**                         | **MIN_AMPLITUDE**    | minimum amplitude

        - Return:
        | Name       | Description
        | ---------- | --------------
        | **job_id** | unique job id

        """

        logger.info('audio_clip: new request')

        # check request form
        if request.method != "POST":
            return BadRequest("Bad Method `%s`. Only POST method is allowed." % request.method)

        if request.headers.get("Content-Type") != 'application/json':
            return BadRequest("Bad Content-Type `%s`. Only application/json Content-Type is allowed." % request.headers)

        # check parameter body
        post_body = request.get_json()

        file_name = post_body.get('file_name', '')
        if file_name == "":
            return BadRequest("Parameter `file_name` is required.")
        elif not file_name.endswith('wav'):
            return BadRequest("Parameter `file_name` should be `wav`: %s" % file_name)
        logger.info(' * parameter `file_path`: %s' % file_name)

        min_interval_sec = post_body.get('min_interval_sec', '')
        valid_flg, value_or_msg = nitro_editor.util.validate_numeric(min_interval_sec, MIN_INTERVAL_SEC, 0.0, 10000, is_float=True)
        if not valid_flg:
            return BadRequest(value_or_msg)
        min_interval_sec = value_or_msg

        min_amplitude = post_body.get('min_amplitude', '')
        valid_flg, value_or_msg = nitro_editor.util.validate_numeric(min_amplitude, MIN_AMPLITUDE, 0.0, 100, is_float=True)
        if not valid_flg:
            return BadRequest(value_or_msg)
        min_amplitude = value_or_msg

        # run process
        job_id = job_status_instance.register_job()
        logger.info(' - job_id: %s' % job_id)
        thread = Thread(target=process, args=[job_id, file_name, min_interval_sec, min_amplitude])
        thread.start()
        return jsonify(job_id=job_id)

    # @app.route("/video_clipping", methods=["POST"])
    # def video_clipping_endpoint():
    #     logger.info('video clipping: new request')
    #
    #     if request.method != "POST":
    #         return jsonify(status="ERROR: Bad Method `%s`. Only POST method is allowed." % request.method)
    #
    #     if request.headers.get("Content-Type") != 'application/json':
    #         return jsonify(status="ERROR: Bad Content-Type `%s`. Only application/json Content-Type is allowed."
    #                               % request.headers)
    #
    #     post_body = request.get_json()
    #     tmp_download_file = TMP_DOWNLOAD_FILE + '.mp4'
    #
    #     def required_param_validate(name):
    #         tmp = post_body.get(name, "")
    #         is_error = False
    #         if tmp == "":
    #             is_error = True
    #             msg = "Error: Parameter `%s` is required." % name
    #             return msg, is_error
    #         if tmp.startswith('http'):
    #             logger.info('download file from %s' % tmp)
    #             urllib.request.urlretrieve(tmp, tmp_download_file)
    #
    #             start = time()
    #             while True:
    #                 if os.path.exists(tmp_download_file):
    #                     break
    #                 if time() - start > 30:
    #                     is_error = True
    #                     msg = 'ERROR: Runtime error, can not download file: %s ' % tmp_download_file
    #                     return msg, is_error
    #             tmp = tmp_download_file
    #             return tmp, is_error
    #         logger.info(' - %s: %s' % (name, str(tmp)))
    #         return tmp, is_error
    #
    #     def param_validate(name, default, min_val, max_val, data_type=float):
    #         param_value = post_body.get(name, default)
    #         is_error = False
    #         if param_value is None:
    #             return param_value
    #
    #         try:
    #             numeric_val = data_type(param_value)
    #         except ValueError:
    #             msg = f'Param "{name}" must be a numeric value between "{min_val}" and "{max_val}"'
    #             is_error = True
    #             return msg, is_error
    #
    #         if numeric_val > max_val or numeric_val < min_val:
    #             msg = f'Param "{name}" must be between {min_val} and {max_val}'
    #             is_error = True
    #             return msg, is_error
    #
    #         logger.info(' - %s: %s' % (name, str(numeric_val)))
    #         return numeric_val, is_error
    #
    #     logger.info('parameters')
    #
    #     output, _is_error = required_param_validate('file_path')
    #     if _is_error:
    #         return jsonify(status='ERROR: %s' % output)
    #     else:
    #         file_path = output
    #
    #     output, _is_error = required_param_validate('output_path')
    #     if _is_error:
    #         return jsonify(status='ERROR: %s' % output)
    #     else:
    #         output_path = output
    #
    #     output, _is_error = param_validate('min_interval_sec', MIN_INTERVAL_SEC, 0.0, 10000, float)
    #     if _is_error:
    #         return jsonify(status='ERROR: %s' % output)
    #     else:
    #         min_interval_sec = output
    #
    #     output, _is_error = param_validate('min_amplitude', MIN_AMPLITUDE, 0.0, 100, float)
    #     if _is_error:
    #         return jsonify(status='ERROR: %s' % output)
    #     else:
    #         min_amplitude = output
    #
    #     logger.info('start process')
    #     thread = Thread(target=process,
    #                     args=[file_path, output_path, min_interval_sec, min_amplitude, tmp_download_file])
    #     thread.start()
    #     return jsonify(status='process started')

    @app.route("/job_status", methods=["GET"])
    def job_status():
        """ get job status """
        if request.method != "GET":
            return BadRequest("Only GET method is allowed.")

        job_id = request.args.get("job_id")
        if job_id == '':
            return BadRequest('`job_id` is required.')
        status = job_status_instance.get_status(job_id)
        return jsonify(status)

    @app.route("/drop_job_status", methods=["GET"])
    def drop_job_status():
        """ drop completed job statuses """
        before = len(job_status_instance.get_job_ids)
        job_status_instance.drop()
        after = len(job_status_instance.get_job_ids)
        return jsonify(status='drop %i job status' % (before - after))

    @app.route("/job_ids", methods=["GET"])
    def job_ids():
        """ get list of job ids """
        return jsonify(job_ids=job_status_instance.get_job_ids)

    @app.route("/drop_file_firebase", methods=["GET"])
    def drop_file_firebase():
        """ drop file in firebase """
        if request.method != "GET":
            return BadRequest("Only GET method is allowed.")

        file_name = request.args.get("file_name")
        try:
            if file_name == '':
                removed = firebase.remove(None)
            else:
                removed = firebase.remove(file_name)
            return jsonify(removed_files=removed)
        except Exception:
            return InternalServerError(traceback.format_exc())

    app.run(host="0.0.0.0", port=PORT, debug=False)


if __name__ == '__main__':
    main()
