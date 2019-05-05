# NITRO
Python library to edit video/audio 

## Get started

```
git clone https://github.com/asahi417/nitro_editor
cd nitro_editor
pip install -e .
```

## API
Run API server 
```
python ./bin/api_nitro_clipping.py
```

Environment variables:

| Environment variable name  | Default | Description                                                                                         |
| -------------------------- | ------- | --------------------------------------------------------------------------------------------------- |
| **PORT**                   | `7001`  | port to host the server on                                                                          |
| **MIN_INTERVAL_SEC**       | `0.2`   | default value of `min_interval_sec`     |
| **MIN_AMPLITUDE**          | `0.1`   | default value of `min_amplitude`     |


### `audio_clipping`
- Description: POST API to truncate wav audio file.
- Endpoint: `audio_clipping`
- Parameters:

| Parameter name                            | Default | Description                                                                         |
| ----------------------------------------- | ------- | ----------------------------------------------------------------------------------- |
| **file_path**<br />_(\* required)_        |  -      | absolute path or url to fetch audio file  |
| **output_path**<br />_(\* required)_      |  -      | absolute path where the modified audio will be saved |
| **min_interval_sec**                      | **MIN_INTERVAL_SEC** | minimum interval of part to exclude (sec) |
| **min_amplitude**                         | **MIN_AMPLITUDE** | minimum amplitude |

- Return:

| Name     | Description                                     |
| --------------- | ----------------------------------------------- |
| **status**      | message  | 

Progress of process for the given audio file can be checked by calling `job_status`. 

### `video_clipping`
- Description: POST API to truncate wav audio file.
- Endpoint: `video_clipping`
- Parameters:

| Parameter name                            | Default | Description                                                                         |
| ----------------------------------------- | ------- | ----------------------------------------------------------------------------------- |
| **file_path**<br />_(\* required)_        |  -      | absolute path or url to fetch audio file  |
| **output_path**<br />_(\* required)_      |  -      | absolute path where the modified audio will be saved |
| **min_interval_sec**                      | **MIN_INTERVAL_SEC** | minimum interval of part to exclude (sec) |
| **min_amplitude**                         | **MIN_AMPLITUDE** | minimum amplitude |

- Return:

| Name     | Description                                     |
| --------------- | ----------------------------------------------- |
| **status**      | message  | 

Progress of process for the given audio file can be checked by calling `job_status`. 


### `job_status`
- Description: Check current job status
- Endpoint: `job_status`
- Return:

| Name     | Description                                     |
| --------------- | ----------------------------------------------- |
| **status**      | job status/error message |
| **status_code** | `0`: no job, `1`: in progress, `-1`: error |


