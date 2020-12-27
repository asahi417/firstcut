# FirstCut
Audio/video editor: detecting silent interval and eliminated them from the original file to compress the audio/video.
- python interface
- API service    

## Get started with Docker
Clone the repo and build docker composer file (see [here](./assets/RUN_WITHOUT_DOCKER.md) for running without docker).

```
git clone https://github.com/asahi417/firstcut
cd firstcut
docker-compose -f docker-compose.yml up
```

The app runs with firebase backend, and so requires
[credentials for connecting to firebase storage](assets/FIREBASE.md)
to be included in [docker-composer](./docker-compose.yml) file.

To deploy the image to gcp project, see [here](assets/DEPLOY_GCP.md).

## Service
### `audio_clip`
- Description: POST API to truncate wav audio file.
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
