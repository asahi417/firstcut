""" Main API hosting """
import json
import os
import logging
import traceback
from threading import Thread
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import firstcut


# Initialization
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')
KEEP_LOG_SEC = int(os.getenv('KEEP_LOG_SEC', '1800'))  # second to keep job id after complete or failed
MAX_SAMPLE_LENGTH = int(os.getenv('MAX_SAMPLE_LENGTH', 30000000))
JOB_MANAGER = firstcut.Status(keep_log_second=KEEP_LOG_SEC)


class CompressInput(BaseModel):
    file_path: str
    export_path: Optional[str] = None


class DenoiseInput(CompressInput):
    min_interval_sec: float = 0.125
    cutoff_ratio: float = 0.85
    max_interval_ratio: int = 0.15
    n_iter: int = 1


class EditInput(DenoiseInput):
    crossfade_sec: float = 0.1
    apply_noise_reduction: bool = False


app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


# Endpoint
@app.get("/")
def read_root():
    return {"What's this?": "Awesome video editing app!"}


@app.post("/plot")
async def process(plot_input: CompressInput):
    if not os.path.exists(plot_input.file_path):
        raise HTTPException(status_code=404, detail='File not found at {}'.format(plot_input.file_path))
    editor = firstcut.Editor(plot_input.file_path, max_sample_length=MAX_SAMPLE_LENGTH)
    if plot_input.export_path is None:
        plot_input.export_path = plot_input.file_path + '.firstcut.plot.png'
    editor.plot_wave(plot_input.export_path)
    return {'job_status': 'plot saved at {}'.format(plot_input.export_path)}


@app.post("/denoise")
async def process(denoise_input: DenoiseInput):
    if not os.path.exists(denoise_input.file_path):
        raise HTTPException(status_code=404, detail='File not found at {}'.format(denoise_input.file_path))

    job_id = JOB_MANAGER.register_job()  # issue job id
    thread = Thread(target=denoise_module, args=[job_id, denoise_input])  # run in background
    thread.start()
    return {'job_id': job_id, 'note': 'See update at `/job_status/{}`'.format(job_id)}


@app.post("/edit")
async def process(edit_input: EditInput):
    if not os.path.exists(edit_input.file_path):
        raise HTTPException(status_code=404, detail='File not found at {}'.format(edit_input.file_path))
    job_id = JOB_MANAGER.register_job()  # issue job id
    thread = Thread(target=edit_module, args=[job_id, edit_input])  # run in background
    thread.start()
    return {'job_id': job_id, 'note': 'See update at `/job_status/{}`'.format(job_id)}


@app.post("/compress")
async def process(compress_input: CompressInput):
    if not os.path.exists(compress_input.file_path):
        raise HTTPException(status_code=404, detail='File not found at {}'.format(compress_input.file_path))
    job_id = JOB_MANAGER.register_job()  # issue job id
    thread = Thread(target=edit_module, args=[job_id, compress_input, True])  # run in background
    thread.start()
    return {'job_id': job_id, 'note': 'See update at `/job_status/{}`'.format(job_id)}


def edit_module(job_id: str, edit_input: EditInput, skip_editing: bool = False):
    try:
        if edit_input.export_path is None:
            edit_input.export_path = '.'.join(edit_input.file_path.split('.')[:-1]) + '.firstcut.{}'.format(job_id)

        JOB_MANAGER.update(status='initialize model', job_id=job_id, progress=0)
        editor = firstcut.Editor(edit_input.file_path, max_sample_length=MAX_SAMPLE_LENGTH)

        if not skip_editing:
            JOB_MANAGER.update(status='start editing file', job_id=job_id, progress=10)
            config = {'min_interval_sec': edit_input.min_interval_sec,
                      'cutoff_ratio': edit_input.cutoff_ratio,
                      'crossfade_sec': edit_input.crossfade_sec}
            if edit_input.apply_noise_reduction:
                config.update({'apply_noise_reduction': edit_input.apply_noise_reduction,
                               'max_interval_ratio': edit_input.max_interval_ratio, 'n_iter': edit_input.n_iter})
            editor.amplitude_clipping(**config)
            config_file = edit_input.export_path + '.config.json'
            with open(config_file, 'w') as f:
                json.dump(config, f)

            JOB_MANAGER.update(job_id=job_id, progress=70, status='exporting file to {}'.format(edit_input.export_path))
            export_file = editor.export_file(edit_input.export_path)

            # update job status
            JOB_MANAGER.complete(
                job_id=job_id, file_exported=export_file, file_source=edit_input.file_path, config_file=config_file)
        else:
            # update job status
            JOB_MANAGER.complete(
                job_id=job_id, file_exported=editor.export_file(edit_input.export_path), file_source=edit_input.file_path)

    except Exception:
        JOB_MANAGER.error(job_id=job_id, error_message=traceback.format_exc())
        logging.exception('Error: {}'.format(job_id))


def denoise_module(job_id: str, denoise_input: DenoiseInput):
    try:
        if denoise_input.export_path is None:
            denoise_input.export_path = '.'.join(denoise_input.file_path.split('.')[:-1]) + '.firstcut.denoise.{}.wav'.format(job_id)

        JOB_MANAGER.update(status='initialize model', job_id=job_id, progress=0)
        editor = firstcut.Editor(denoise_input.file_path, max_sample_length=MAX_SAMPLE_LENGTH)

        JOB_MANAGER.update(status='start editing file', job_id=job_id, progress=10)
        editor.noise_reduction(
            min_interval_sec=denoise_input.min_interval_sec,
            cutoff_ratio=denoise_input.cutoff_ratio,
            max_interval_ratio=denoise_input.max_interval_ratio,
            n_iter=denoise_input.n_iter,
            export_audio=denoise_input.export_path)

        # update job status
        JOB_MANAGER.complete(job_id=job_id, file_audio=denoise_input.export_path)
    except Exception:
        JOB_MANAGER.error(job_id=job_id, error_message=traceback.format_exc())
        logging.exception('Error: {}'.format(job_id))


@app.get("/job_status/{job_id}")
def read_item(job_id: str):
    return JOB_MANAGER.get_status(job_id)


@app.get("/show_jobs/")
def read_item():
    return {'job_ids': JOB_MANAGER.get_job_ids}


