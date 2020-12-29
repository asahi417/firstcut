# FirstCut
Audio/video editor: detecting silent interval and eliminated them from the original audio/video.
- python interface
- API service

## Get started
```shell script
git clone https://github.com/asahi417/firstcut
cd firstcut
```

### Docker
Build docker composer.

```shell script
docker-compose -f docker-compose.yml up
```

The app runs with firebase backend, so requires [firebase credentials](./assets/FIREBASE.md).
To deploy the image to gcp project, see [here](assets/DEPLOY_GCP.md).

### Commandline

```shell script
pip install .
python api.py
```
Configuration can be changed via environment variables. 

| Environment variable name  | Default | Description                                                                                         |
| -------------------------- | ------- | --------------------------------------------------------------------------------------------------- |
| **PORT**                   | `8008`  | port to host the server on                                                                          |
| **TMP_DIR**                | `./tmp` | directory where the files to be saved |
| **FIREBASE_SERVICE_ACOUNT**|         | service credential |
| **FIREBASE_APIKEY**        |         | apiKey |
| **FIREBASE_AUTHDOMAIN**    |         | authDomain |
| **FIREBASE_DATABASEURL**   |         | databaseURL |
| **FIREBASE_STORAGEBUCKET** |         | storageBucket |
| **FIREBASE_GMAIL**         |         | Gmail account registered to Firebase |
| **FIREBASE_PASSWORD**      |         | password for the Gmail account |

## Service
### `audio_clip`
- Description: POST API to clip audio/video.
- Valid file format: `['mp3', 'wav', 'm4a', 'mp4', 'mov']`
- Parameters:

| Parameter name                            | Default              | Description                           |
| ----------------------------------------- | -------------------- | ------------------------------------- |
| **file_name**<br />_(\* required)_        |  -                   | file name to be processed on firebase |
| **min_interval_sec**                      | 0.12                 | minimum interval of part to exclude (sec) |
| **cutoff_ratio**                          | 0.9                  | cutoff ratio from 0 to 1 |
| **crossfade_sec**                         | 0.1                  | crossfade interval |
 
- Return:

| Name       | Description                                     |
| ---------- | ----------------------------------------------- |
| **job_id** | unique job id  |

Progress of process for the given audio file can be checked by calling `job_status`. 

### `job_status`
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
| **url**             | url for processed file (provided only the job has been completed) |
| **file_name**       | processed file name |


### `job_ids`
- Description: GET API to get list of job id
- Return:

| return name         | Description     |
| ------------------- | --------------- |
| **job_ids**         | list of job ids |


### `drop_job_status`
- Description: GET API to drop completed job status. Server will keep all the job status, unless you request this method. 
- Return:

| return name         | Description    |
| ------------------- | -------------- |
| **status**          | status message |

### `drop_file_firebase`
- Description: GET API to remove file on firebase 
- Parameters:

| Parameter name   | Default | Description                                                                         |
| ---------------- | ------- | ----------------------------------------------------------------------------------- |
| **file_name**    |         | file name to remove, if not provided, remove all the files (`all` to remove all files) |


- Return:

| return name         | Description           |
| ------------------- | --------------------- |
| **removed_files**   | list of removed files |
