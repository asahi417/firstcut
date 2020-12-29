""" Video/Audio clipping API """
import os
import traceback
import logging
from threading import Thread

import firstcut
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.exceptions import BadRequest, InternalServerError

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')

app = Flask(__name__)
CORS(app)

# CONFIG
TMP_DIR = './tmp'  # directory where audio/video files are temporarily stored
KEEP_LOG_SEC = int(os.getenv('KEEP_LOG_SEC', '180'))
PORT = int(os.getenv("PORT", "8008"))
FIREBASE_SERVICE_ACCOUNT = os.getenv('FIREBASE_SERVICE_ACCOUNT', None)
FIREBASE_APIKEY = os.getenv('FIREBASE_APIKEY', None)
FIREBASE_AUTHDOMAIN = os.getenv('FIREBASE_AUTHDOMAIN', None)
FIREBASE_DATABASEURL = os.getenv('FIREBASE_DATABASEURL', None)
FIREBASE_STORAGEBUCKET = os.getenv('FIREBASE_STORAGEBUCKET', None)
FIREBASE_GMAIL = os.getenv('FIREBASE_GMAIL', None)
FIREBASE_PASSWORD = os.getenv('FIREBASE_PASSWORD', None)


def main():
    """ Main API server """
    job_status_instance = firstcut.Status(keep_log_second=KEEP_LOG_SEC)

    # connect to firebaase
    try:
        firebase = firstcut.FireBaseConnector(
                apiKey=FIREBASE_APIKEY,
                authDomain=FIREBASE_AUTHDOMAIN,
                databaseURL=FIREBASE_DATABASEURL,
                storageBucket=FIREBASE_STORAGEBUCKET,
                serviceAccount=FIREBASE_SERVICE_ACCOUNT,
                gmail=FIREBASE_GMAIL,
                password=FIREBASE_PASSWORD)
    except Exception:
        logging.exception('run without FireBase')
        firebase = None

    def _audio_clip(job_id, file_name, interval, ratio, crossfade, max_sample):
        """ Audio clipping function

         Parameter
        ------------
        job_id: unique job id
        file_name: file name to process
        interval: min_interval_sec
        ratio: cutoff_ratio
        crossfade: crossfade_sec
        """
        try:
            logging.info('validate file_name')
            job_status_instance.update(job_id=job_id, progress=0, status='validate file_name')
            basename = os.path.basename(file_name).split('.')
            raw_format = basename[-1]
            name = '.'.join(basename[:-1])
            if firebase is None:
                # referring local file
                if not os.path.exists(file_name):
                    raise ValueError('file not found: {}'.format(file_name))
                path_file = file_name
            else:
                path_file = os.path.join(TMP_DIR, '{}_{}_raw.{}'.format(name, job_id, raw_format))
                if not os.path.exists(path_file):
                    msg = 'download {} from firebase to {}'.format(file_name, path_file)
                    job_status_instance.update(job_id=job_id, status=msg)
                    logging.info(msg)
                    firebase.download(file_name=file_name, path=path_file)

            job_status_instance.update(status='start processing', job_id=job_id, progress=20)
            logging.info('start processing')
            editor = firstcut.Editor(path_file, max_sample_length=max_sample)
            editor.amplitude_clipping(min_interval_sec=interval, cutoff_ratio=ratio, crossfade_sec=crossfade)

            if editor.is_edited:
                msg = 'save tmp folder: {}'.format(TMP_DIR)
                job_status_instance.update(job_id=job_id, progress=70, status=msg)
                logging.info(msg)
                base_name = '{}_{}_processed'.format(name, job_id)
                if firebase is None:
                    file_name = editor.export(os.path.join(TMP_DIR, base_name))
                    url = ''
                else:
                    logging.info('upload to firebase')
                    job_status_instance.update(job_id=job_id, progress=75, status='upload to firebase')
                    file_name = editor.export(os.path.join(TMP_DIR, base_name))
                    url = firebase.upload(file_path=file_name)
                to_clean = os.path.join(TMP_DIR, '{}_{}_*'.format(name, job_id))
                msg = 'clean local storage: {}'.format(to_clean)
                logging.info(msg)
                job_status_instance.update(job_id=job_id, progress=95, status=msg)
                os.system('rm -rf {}'.format(to_clean))
            else:
                url = '' if firebase is None else firebase.get_url(file_name)
            # update job status
            job_status_instance.complete(job_id=job_id, url=url, file_name=file_name)

        except Exception:
            job_status_instance.error(job_id=job_id, error_message=traceback.format_exc())
            logging.exception('raise error')

    @app.route("/audio_clip", methods=["POST"])
    def audio_clip():
        """ Audio clip API endpoint """

        logging.info('audio_clip: new request')

        # check request form
        if request.method != "POST":
            return BadRequest("Bad Method `{}`. Only POST method is allowed.".format(request.method))

        if request.headers.get("Content-Type") != 'application/json':
            return BadRequest("Bad Content-Type `{}`. Only application/json is allowed.".format(request.headers))

        # check parameter body
        post_body = request.get_json()

        file_name = post_body.get('file_name', '')
        if file_name == "":
            return BadRequest('Parameter `file_name` is required')
        if not len(os.path.basename(file_name).split('.')) > 1:
            return BadRequest('file dose not have any identifiers: {}'.format(file_name))
        logging.info(' * parameter `file_name`: {}'.format(file_name))

        # parameter
        min_interval_sec = post_body.get('min_interval_sec', '0.12')
        min_interval_sec, msg = firstcut.validate_numeric(min_interval_sec, 0.0, 10000, is_float=True)
        if min_interval_sec is None:
            return BadRequest(msg)
        logging.info(' * parameter `min_interval_sec`: {}'.format(min_interval_sec))

        # parameter
        cutoff_ratio = post_body.get('cutoff_ratio', '0.9')
        cutoff_ratio, msg = firstcut.validate_numeric(cutoff_ratio, 0.0, 1.0, is_float=True)
        if cutoff_ratio is None:
            return BadRequest(msg)
        logging.info(' * parameter `cutoff_ratio`: {}'.format(cutoff_ratio))

        # parameter
        max_sample_length = post_body.get('max_sample_length ', '1200000')
        max_sample_length, msg = firstcut.validate_numeric(max_sample_length, 0, 1200000)
        if max_sample_length is None:
            return BadRequest(msg)
        logging.info(' * parameter `max_sample_length`: {}'.format(max_sample_length))

        # parameter
        crossfade_sec = post_body.get('crossfade_sec', '0.1')
        crossfade_sec, msg = firstcut.validate_numeric(crossfade_sec, 0.0, 10000, is_float=True)
        if crossfade_sec is None:
            return BadRequest(msg)
        logging.info(' * parameter `crossfade_sec`: {}'.format(crossfade_sec))

        # run process
        job_id = job_status_instance.register_job()
        logging.info(' - job_id: {}'.format(job_id))
        args = [job_id, file_name, min_interval_sec, cutoff_ratio, crossfade_sec, max_sample_length]
        thread = Thread(target=_audio_clip, args=args)
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
        return jsonify(status='drop {} job status'.format(before - after))

    @app.route("/job_ids", methods=["GET"])
    def job_ids():
        """ get list of job ids """
        return jsonify(job_ids=job_status_instance.get_job_ids)

    @app.route("/drop_file_firebase", methods=["GET"])
    def drop_file_firebase():
        """ drop file in firebase """
        if request.method != "GET":
            return BadRequest("Only GET method is allowed.")
        if firebase is None:
            return BadRequest("Run without firebase backend")
        file_name = request.args.get("file_name")

        try:
            if file_name == 'all':
                logging.info('remove all files on firebase')
                removed = firebase.remove(None)
            elif file_name == '':
                return BadRequest('`job_id` is required.')
            else:
                logging.info('remove {} on firebase'.format(file_name))
                removed = firebase.remove(file_name)
            return jsonify(removed_files=removed)
        except Exception:
            logging.exception("get error during process")
            return InternalServerError(traceback.format_exc())

    app.run(host="0.0.0.0", port=PORT, debug=False)


if __name__ == '__main__':
    main()
