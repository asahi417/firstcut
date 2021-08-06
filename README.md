# FirstCut
Audio/video editor: detecting silent interval and eliminated them from the original audio/video.
- python interface
- API service

## Get started
```shell script
git clone https://github.com/asahi417/firstcut
cd firstcut
pip install .
```

## API Service
- ***Build with docker composer***

```shell script
docker-compose -f docker-compose.yml up
```

The app runs with firebase backend, so requires [firebase credentials](asset/backup/FIREBASE.md).
To deploy the image to gcp project, see [here](asset/backup/DEPLOY_GCP.md).

- ***Commandline***
On mac OS, 
```shell script
brew install llvm@9
brew install ffmpeg
pip install .
uvicorn app:app --reload
```
while Linux, 

```shell script
apt-get install llvm@9
apt-get install ffmpeg
pip install .
uvicorn app:app --reload
``` 

Configuration can be changed via environment variables. 

| Environment variable name  | Default | Description                                                                                         |
| -------------------------- | ------- | --------------------------------------------------------------------------------------------------- |
| **PORT**                   | `8008`  | port number |
| **KEEP_LOG_SEC**           | `1800`  | time to keep the job id after completed or failed                                                                          |
| **MAX_SAMPLE_LENGTH**      |`30000000`| max sample length to process                                                                          |

### `edit`
- Description: POST API to remove silent parts from audio/video.
- Valid file format: `['mp3', 'wav', 'm4a', 'mp4', 'mov']`
- Parameters:

| Parameter name                            | Default              | Description                           |
| ----------------------------------------- | -------------------- | ------------------------------------- |
| **file_path**<br />_(\* required)_        |  -                   | file path to the audio/video |
| **export_path**                           | None                 | path to export processed file (if not given, the processed file is saved at `{file_path}.firstcut.{job_id}`) |
| **min_interval_sec**                      | 0.12                 | minimum interval of part to exclude (sec) |
| **cutoff_ratio**                          | 0.9                  | cutoff ratio from 0 to 1 |
| **crossfade_sec**                         | 0.1                  | crossfade interval |
| **apply_noise_reduction**                 | false                | apply noise reduction before editing |
| **max_interval_ratio**                    | 0.15                 | parameter for noise reduction |
| **n_iter**                                | 1                    | parameter for noise reduction |
 
- Return:

| Name       | Description                                     |
| ---------- | ----------------------------------------------- |
| **job_id** | unique job id  |

The progress of the file can be checked by calling `job_status`.


### `denoise`
- Description: POST API to perform noise reduction on audio/video.
- Valid file format: `['mp3', 'wav', 'm4a', 'mp4', 'mov']`
- Parameters:

| Parameter name                            | Default              | Description                           |
| ----------------------------------------- | -------------------- | ------------------------------------- |
| **file_path**<br />_(\* required)_        |  -                   | file path to the audio/video |
| **export_path**                           | None                 | path to export processed file (if not given, the processed file is saved at `{file_path}.firstcut.{job_id}`) |
| **min_interval_sec**                      | 0.12                 | minimum interval of part to exclude (sec) |
| **cutoff_ratio**                          | 0.9                  | cutoff ratio from 0 to 1 |
| **max_interval_ratio**                    | 0.15                 | parameter for noise reduction |
| **n_iter**                                | 1                    | parameter for noise reduction |
 
- Return:

| Name       | Description                                     |
| ---------- | ----------------------------------------------- |
| **job_id** | unique job id  |

The progress of the file can be checked by calling `job_status`.


### `compress`
- Description: POST API to reduce file size of audio/video.
- Valid file format: `['mp3', 'wav', 'm4a', 'mp4', 'mov']`
- Parameters:

| Parameter name                            | Default              | Description                           |
| ----------------------------------------- | -------------------- | ------------------------------------- |
| **file_path**<br />_(\* required)_        |  -                   | file path to the audio/video |
| **export_path**                           | None                 | path to export processed file (if not given, the processed file is saved at `{file_path}.firstcut.{job_id}`) |
 
- Return:

| Name       | Description                                     |
| ---------- | ----------------------------------------------- |
| **job_id** | unique job id  |

The progress of the file can be checked by calling `job_status`.


### `show_jobs`
- Description: GET API for job status
- Parameters:

| Parameter name                  | Default | Description                                                                         |
| ------------------------------- | ------- | ----------------------------------------------------------------------------------- |
| **job_id**<br />_(\* required)_ |         | job id |

- Return:

| return name         | Description                                     |
| ------------------- | ----------------------------------------------- |
| **status**          | status |
| **progress**        | progress percentage from 0 up to 100 |
| **status_code**     | `{'1': job in progress, '-1': error, '0': job_completed}` |
| **elapsed_time**    | elapsed time after starting process |
| **file_name**       | processed file name |


### `job_ids`
- Description: GET API to get list of job id
- Return:

| return name         | Description     |
| ------------------- | --------------- |
| **job_ids**         | list of job ids |


## Python interface
It works as an python library as well where one can simply apply filtering and editing for a audio/video file.  

```python
import firstcut
file_path = './sample_data/vc_1.mp3'
editor = firstcut.Editor(file_path)
editor.amplitude_clipping(min_interval_sec=0.5, cutoff_ratio=0.9)
```
