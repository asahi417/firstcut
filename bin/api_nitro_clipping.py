""" Video/Audio clipping API """

import nitro_editor
from threading import Thread
import traceback
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.exceptions import BadRequest, InternalServerError

app = Flask(__name__)
CORS(app)

# CONFIG
TMP_DIR = '/tmp'  # directory where audio/video files are temporarily stored
PORT = int(os.getenv("PORT", "8008"))
MIN_INTERVAL_SEC = float(os.getenv("MIN_INTERVAL_SEC", "0.12"))
CUTOFF_RATIO = float(os.getenv("CUTOFF_RATIO", "0.9"))
CROSSFADE_SEC = float(os.getenv("CROSSFADE_SEC", "0.1"))
CUTOFF_METHOD = os.getenv("CUTOFF_METHOD", "percentile")
KEEP_LOG_SEC = int(os.getenv('KEEP_LOG_SEC', '180'))
FIREBASE_SERVICE_ACCOUNT = os.getenv('FIREBASE_SERVICE_ACCOUNT', None)
FIREBASE_APIKEY = os.getenv('FIREBASE_APIKEY', None)
FIREBASE_AUTHDOMAIN = os.getenv('FIREBASE_AUTHDOMAIN', None)
FIREBASE_DATABASEURL = os.getenv('FIREBASE_DATABASEURL', None)
FIREBASE_STORAGEBUCKET = os.getenv('FIREBASE_STORAGEBUCKET', None)
FIREBASE_GMAIL = os.getenv('FIREBASE_GMAIL', None)
FIREBASE_PASSWORD = os.getenv('FIREBASE_PASSWORD', None)
MAX_LENGTH_SEC = int(os.getenv('MAX_LENGTH_SEC', 1200))


def main():
    """ Main API server """
    job_status_instance = nitro_editor.job_status.Status(keep_log_second=KEEP_LOG_SEC)
    logger = nitro_editor.util.create_log()

    def logging(_msg,
                _job_id: str = None,
                debug: bool = False,
                error: bool = False,
                progress: float = None):
        """ Logger (as default INFO)

         Parameter
        -----------
        _msg: str
            log message
        _job_id: str
            unique job id
        debug: bool
            log as debug
        error: bool
            log as error
        """
        if error:
            if _job_id is not None:
                job_status_instance.error(job_id=_job_id, error_message=_msg)
            logger.error('job_id `%s` raises InternalServerError\n %s' % (_job_id, _msg))
        else:
            if _job_id is not None:
                job_status_instance.update(job_id=_job_id, status=_msg, progress=progress)
            if debug:
                logger.debug(_msg)
            else:
                logger.info(_msg)

    # connect to firebaase
    try:
        firebase = nitro_editor.util.FireBaseConnector(
                apiKey=FIREBASE_APIKEY,
                authDomain=FIREBASE_AUTHDOMAIN,
                databaseURL=FIREBASE_DATABASEURL,
                storageBucket=FIREBASE_STORAGEBUCKET,
                serviceAccount=FIREBASE_SERVICE_ACCOUNT,
                gmail=FIREBASE_GMAIL,
                password=FIREBASE_PASSWORD
            )
    except Exception:
        logger.debug(traceback.format_exc())
        logger.debug('API will run local mode')
        firebase = None

    def audio_clip_process(job_id,
                           file_name,
                           min_interval_sec,
                           ratio,
                           crossfade_sec,
                           run_local=False):
        """ Audio clip process function

         Parameter
        ------------
        job_id: str
            unique job id
        file_name: str
            file name to process
        min_interval_sec: float
            minimum interval seconds
        ratio: float
            ratio to retrieve
        crossfade_sec: float
        """
        try:
            logging('validate file_name', job_id, debug=True, progress=0)
            basename = os.path.basename(file_name).split('.')
            raw_format = basename[-1]
            name = '.'.join(basename[:-1])
            if run_local:
                # referring local file
                if not os.path.exists(file_name):
                    raise ValueError('file not found: %s' % file_name)
                path_file = file_name
            else:
                path_file = os.path.join(TMP_DIR, '%s_%s_raw.%s' % (name, job_id, raw_format))
                if not os.path.exists(path_file):
                    logging('download %s from firebase to %s' % (file_name, path_file), job_id, debug=True)
                    firebase.download(file_name=file_name, path=path_file)

            logging('start processing', job_id, debug=True, progress=20)
            editor = nitro_editor.audio.AudioEditor(path_file, cutoff_method=CUTOFF_METHOD)
            if editor.length_sec > MAX_LENGTH_SEC:
                logging('Too long length: %i sec > %i sec' % (editor.length_sec, MAX_LENGTH_SEC), job_id, error=True)
                return

            flg_processed = editor.amplitude_clipping(
                min_interval_sec=min_interval_sec, ratio=ratio, crossfade_sec=crossfade_sec)

            if flg_processed or editor.is_mov:
                logging('save tmp folder: %s' % TMP_DIR, job_id, debug=True, progress=70)
                path_save = editor.write(os.path.join(TMP_DIR, '%s_%s_processed' % (name, job_id)))
                if run_local:
                    url = path_save
                else:
                    logging('upload to firebase', job_id, debug=True, progress=75)
                    url = firebase.upload(file_path=path_save)
                    to_clean = os.path.join(TMP_DIR, '%s_%s_*' % (name, job_id))
                    logging('clean local storage: %s' % to_clean, job_id, debug=True, progress=95)
                    os.system('rm -rf %s' % to_clean)
            else:
                if run_local:
                    url = file_name
                else:
                    url = firebase.get_url(file_name)
            # update job status
            job_status_instance.complete(job_id=job_id, url=url)
            return

        except Exception:
            logging(traceback.format_exc(), job_id, error=True)

    @app.route("/audio_clip", methods=["POST"])
    def audio_clip():
        """ Audio clip API endpoint """

        logging('audio_clip: new request')

        # check request form
        if request.method != "POST":
            return BadRequest("Bad Method `%s`. Only POST method is allowed." % request.method)

        if request.headers.get("Content-Type") != 'application/json':
            return BadRequest("Bad Content-Type `%s`. Only application/json Content-Type is allowed." % request.headers)

        # check parameter body
        post_body = request.get_json()

        file_name = post_body.get('file_name', '')
        if file_name == "":
            return BadRequest('Parameter `file_name` is required')
        if not len(os.path.basename(file_name).split('.')) > 1:
            return BadRequest('file dose not have any identifiers: %s' % file_name)
        logging(' * parameter `file_name`: %s' % file_name)

        # parameter
        min_interval_sec = post_body.get('min_interval_sec', '')
        valid_flg, value_or_msg = nitro_editor.util.validate_numeric(
            min_interval_sec, MIN_INTERVAL_SEC, 0.0, 10000, is_float=True)
        if not valid_flg:
            return BadRequest(value_or_msg)
        min_interval_sec = value_or_msg
        logging(' * parameter `min_interval_sec`: %s' % str(min_interval_sec))

        # parameter
        cutoff_ratio = post_body.get('cutoff_ratio', '')
        valid_flg, value_or_msg = nitro_editor.util.validate_numeric(
            cutoff_ratio, CUTOFF_RATIO, 0.0, 1.0, is_float=True)
        if not valid_flg:
            return BadRequest(value_or_msg)
        cutoff_ratio = value_or_msg
        logging(' * parameter `cutoff_ratio`: %s' % str(cutoff_ratio))

        # parameter
        crossfade_sec = post_body.get('crossfade_sec', '')
        valid_flg, value_or_msg = nitro_editor.util.validate_numeric(
            crossfade_sec, CROSSFADE_SEC, 0.0, 10000, is_float=True)
        if not valid_flg:
            return BadRequest(value_or_msg)
        crossfade_sec = value_or_msg
        logging(' * parameter `crossfade_sec`: %s' % str(crossfade_sec))

        # run local
        run_local = firebase is None

        # run process
        job_id = job_status_instance.register_job()
        logging(' - job_id: %s' % job_id)
        thread = Thread(target=audio_clip_process,
                        args=[job_id, file_name, min_interval_sec, cutoff_ratio, crossfade_sec, run_local])
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
                logging('remove all files on firebase')
                removed = firebase.remove(None)
            elif file_name == '':
                return BadRequest('`job_id` is required.')
            else:
                logging('remove %s files on firebase' % str(file_name))
                removed = firebase.remove(file_name)
            return jsonify(removed_files=removed)
        except Exception:
            return InternalServerError(traceback.format_exc())

    app.run(host="0.0.0.0", port=PORT, debug=False)


if __name__ == '__main__':
    main()
