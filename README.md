# Nitro-editor
Audio/video clipping service by detecting silent interval automatically and eliminated them from
the original file (eg, [raw sound](./sample_files/sample_0.wav) -> [processed sound](./sample_files/sample_0_edit.wav)).
Firebase storage is used as backend data I/O.  

## Get started with Docker
Clone the repo

```
git clone https://github.com/asahi417/nitro_editor
cd nitro_editor
```

[Nitro-editor requires credentials for connecting to firebase storage.](./FIREBASE.md)
Once you've setup [docker-compose file](./docker-compose.yml), build and run docker-composer.

```
docker-compose -f docker-compose.yml up       
```

## Service
### `audio_clip`
- Description: POST API to truncate wav audio file.
- Sample: `curl -i -H "Content-Type: application/json" -X POST -d '{"file_name": "sample_0.wav"}' http://0.0.0.0:8008/audio_clip`
- Parameters:

| Parameter name                            | Default              | Description                           |
| ----------------------------------------- | -------------------- | ------------------------------------- |
| **file_name**<br />_(\* required)_        |  -                   | file name to be processed on firebase |
| **file_path**<br />_(\* required)_        |  -                   | absolute file path to local file |
| **min_interval_sec**                      | **MIN_INTERVAL_SEC** | minimum interval of part to exclude (sec) |
| **cutoff_ratio**                          | **CUTOFF_RATIO**     | cutoff ratio from 0 to 1 |

Either **file_name** or **file_path** is required.

- Valid file format: `['mp3', 'wav', 'm4a', 'mp4']` 

- Return:

| Name       | Description                                     |
| ---------- | ----------------------------------------------- |
| **job_id** | unique job id  |

Progress of process for the given audio file can be checked by calling `job_status`. 

### `job_status`
- Description: GET API for job status
- Sample" `curl http://0.0.0.0:8008/job_status\?job_id\=zqtlnxepvd`
- Parameters:

| Parameter name                  | Default | Description                                                                         |
| ------------------------------- | ------- | ----------------------------------------------------------------------------------- |
| **job_id**<br />_(\* required)_ |         | job id |

- Return:

| return name         | Description                                     |
| ------------------- | ----------------------------------------------- |
| **status**          | status |
| **status_code**     | `{'1': job in progress, '-1': error, '0': job_completed}` |
| **elapsed_time**    | elapsed time after starting process |
| **url**             | url for processed file (provided only the job has been completed) |


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


## Others
### Build by pip
Instead of build by docker-compose, one can manually build with pip and run the script to launch 
API server

1. ***Set up environment variables***  
Environment variables:

| Environment variable name  | Default | Description                                                                                         |
| -------------------------- | ------- | --------------------------------------------------------------------------------------------------- |
| **PORT**                   | `8008`  | port to host the server on                                                                          |
| **MIN_INTERVAL_SEC**       | `0.2`   | minimum interval of part to exclude (sec) |
| **MIN_AMPLITUDE**          | `0.1`   | minimum amplitude |
| **FIREBASE_SERVICE_ACOUNT**|         | path to serviceAccount file |
| **FIREBASE_APIKEY**        |         | apiKey |
| **FIREBASE_AUTHDOMAIN**    |         | authDomain |
| **FIREBASE_DATABASEURL**   |         | databaseURL |
| **FIREBASE_STORAGEBUCKET** |         | storageBucket |
| **FIREBASE_GMAIL**         |         | Gmail account registered to Firebase |
| **FIREBASE_PASSWORD**      |         | password for the Gmail account |

2. ***install ffmpeg***  
On Mac
```
brew install ffmpeg 
```
On ubuntu 
```
sudo apt install ffmpeg
```

3. ***install & run API server***    
```
pip install -e .
python ./bin/api_nitro_clipping.py
```
