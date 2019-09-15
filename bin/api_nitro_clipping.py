""" Video/Audio clipping API """

import nitro_editor
from threading import Thread
import traceback
import os
import argparse
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.exceptions import BadRequest, InternalServerError

app = Flask(__name__)
CORS(app)

ROOT_DIR = os.path.expanduser("~")

PORT = int(os.getenv("PORT", "8008"))
MIN_INTERVAL_SEC = float(os.getenv("MIN_INTERVAL_SEC", "0.2"))
CUTOFF_RATIO = float(os.getenv("CUTOFF_RATIO", "0.7"))
CUTOFF_METHOD = os.getenv("CUTOFF_METHOD", "percentile")
KEEP_LOG_SEC = int(os.getenv('KEEP_LOG_SEC', '180'))

FIREBASE_SERVICE_ACOUNT = os.getenv('FIREBASE_SERVICE_ACOUNT', None)
FIREBASE_APIKEY = os.getenv('FIREBASE_APIKEY', None)
FIREBASE_AUTHDOMAIN = os.getenv('FIREBASE_AUTHDOMAIN', None)
FIREBASE_DATABASEURL = os.getenv('FIREBASE_DATABASEURL', None)
FIREBASE_STORAGEBUCKET = os.getenv('FIREBASE_STORAGEBUCKET', None)

FIREBASE_GMAIL = os.getenv('FIREBASE_GMAIL', None)
FIREBASE_PASSWORD = os.getenv('FIREBASE_PASSWORD', None)

LOG = nitro_editor.util.create_log()


def main(debug_mode: bool=False):
    job_status_instance = nitro_editor.job_status.Status(keep_log_second=KEEP_LOG_SEC)

    def logging(_msg, _job_id, debug: bool = False, error: bool = False):
        if error:
            job_status_instance.error(job_id=_job_id, error_message=_msg)
            LOG.error('job_id `%s` raises InternalServerError\n %s' % (_job_id, _msg))
        else:
            job_status_instance.update(job_id=_job_id, status=' - uploading processed data')
            if debug:
                LOG.debug(_msg)
            else:
                LOG.info(_msg)

    if debug_mode:
        LOG.warn('No connection to firebase: local test mode')
        firebase = None
    else:
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
    tmp_storage = os.path.join(ROOT_DIR, 'nitro_editor_data', 'tmp_files')
    if not os.path.exists(tmp_storage):
        os.makedirs(tmp_storage, exist_ok=True)

    def process(job_id,
                file_name,
                min_interval_sec,
                ratio,
                if_local):
        try:
            logging('validate file_name', job_id, debug=True)
            basename = os.path.basename(file_name)
            name, identifier = basename.split('.')

            if if_local:
                path_file = file_name
            else:
                path_file = os.path.join(tmp_storage, '%s_%s_raw.%s' % (name, job_id, identifier))
                if not os.path.exists(path_file):
                    logging('download %s from firebase to %s' % (file_name, path_file), job_id, debug=True)
                    firebase.download(file_name=file_name, path=path_file)

            path_save = os.path.join(tmp_storage, '%s_%s_processed.%s' % (name, job_id, identifier))

            logging('start processing', job_id, debug=True)
            editor = nitro_editor.audio.AudioEditor(path_file, cutoff_method=CUTOFF_METHOD)
            flg_processed = editor.amplitude_clipping(min_interval_sec=min_interval_sec, ratio=ratio)
            if not flg_processed:
                if if_local:
                    url = file_name
                else:
                    url = firebase.get_url(file_name)
            else:
                logging('save tmp folder: %s' % tmp_storage, job_id, debug=True)
                editor.write(path_save)
                if if_local:
                    url = path_save
                else:
                    logging('upload to firebase', job_id, debug=True)
                    url = firebase.upload(file_path=path_save)
                    to_clean = os.path.join(tmp_storage, '%s_%s_*' % (name, job_id))
                    logging('clean local storage: %s' % to_clean, job_id, debug=True)
                    os.system('rm -rf %s' % to_clean)

            # update job status
            job_status_instance.complete(job_id=job_id, url=url)
            return

        except Exception:
            logging(traceback.format_exc(), job_id, error=True)

    @app.route("/audio_clip", methods=["POST"])
    def audio_clip():
        """ Audio clip API endpoint

        - Description: POST API to truncate wav audio file.
        - Endpoint: `audio_clip`
        - Parameters:

        | Parameter name                      | Default              | Description
        | ----------------------------------- | -------------------- | -------------------------------
        | **file_name**<br />_(\* required)_  |  -                   | file name in firebase project
        | **file_path**<br />_(\* required)_  |  -                   | local file path
        | **min_interval_sec**                | **MIN_INTERVAL_SEC** | minimum interval of part to exclude (sec)
        | **cutoff_ratio**                    | **CUTOFF_RATIO**     | cutoff ratio from 0 to 1

        - Return:
        | Name       | Description
        | ---------- | --------------
        | **job_id** | unique job id
        """

        LOG.info('audio_clip: new request')

        # check request form
        if request.method != "POST":
            return BadRequest("Bad Method `%s`. Only POST method is allowed." % request.method)

        if request.headers.get("Content-Type") != 'application/json':
            return BadRequest("Bad Content-Type `%s`. Only application/json Content-Type is allowed." % request.headers)

        # check parameter body
        post_body = request.get_json()

        file_name = post_body.get('file_name', '')
        file_path = post_body.get('file_path', '')
        if file_name != "":
            if firebase is None:
                return BadRequest('No connection to Firebase, can not use `file_name` option')
            _file = file_name
            if_local = False
        elif file_path != "":
            _file = file_path
            if_local = True
        else:
            return BadRequest("either `file_name` or `file_path` should be provided")
        if not len(os.path.basename(_file).split('.')) > 1:
            return BadRequest('file dose not have any identifiers: %s' % _file)
        LOG.info(' * parameter `file`: %s' % _file)

        min_interval_sec = post_body.get('min_interval_sec', '')
        valid_flg, value_or_msg = nitro_editor.util.validate_numeric(min_interval_sec, MIN_INTERVAL_SEC, 0.0, 10000, is_float=True)
        if not valid_flg:
            return BadRequest(value_or_msg)
        min_interval_sec = value_or_msg

        cutoff_ratio = post_body.get('cutoff_ratio', '')
        valid_flg, value_or_msg = nitro_editor.util.validate_numeric(cutoff_ratio, CUTOFF_RATIO, 0.0, 1.0, is_float=True)
        if not valid_flg:
            return BadRequest(value_or_msg)
        cutoff_ratio = value_or_msg

        # run process
        job_id = job_status_instance.register_job()
        LOG.info(' - job_id: %s' % job_id)
        thread = Thread(target=process, args=[job_id, _file, min_interval_sec, cutoff_ratio, if_local])
        thread.start()
        return jsonify(job_id=job_id)

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
            if file_name == 'all':
                LOG.info('remove all files on firebase')
                removed = firebase.remove(None)
            elif file_name == '':
                return BadRequest('`job_id` is required.')
            else:
                LOG.info('remove %s files on firebase' % str(file_name))
                removed = firebase.remove(file_name)
            return jsonify(removed_files=removed)
        except Exception:
            return InternalServerError(traceback.format_exc())

    app.run(host="0.0.0.0", port=PORT, debug=False)


def get_options():
    parser = argparse.ArgumentParser(description='clipping API', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--debug', help='debug mode', action='store_true')
    return parser.parse_args()


if __name__ == '__main__':
    args = get_options()
    main(args.debug)
