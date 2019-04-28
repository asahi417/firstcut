# Audio file editor
Python audio file editing library 

## Get started
```
git clone https://github.com/asahi417/audio_editor
cd audio_editor
pip install -e .
```

## API
Run API server 
```
python ./bin/api_audio_truncation.py
```

Environment variables:

| Environment variable name  | Default | Description                                                                                         |
| -------------------------- | ------- | --------------------------------------------------------------------------------------------------- |
| **PORT**                   | `7001`  | port to host the server on                                                                          |
| **MIN_INTERVAL_SEC**       | `0.2`   | default value of `min_interval_sec`     |
| **MIN_AMPLITUDE**          | `0.1`   | default value of `min_amplitude`     |
| **ROOT_DIR**               | `{HOME}` | root dir of audio files  |


### `wav_truncation`
- Description: POST API to truncate wav audio file.
- Endpoint: `wav_truncation`
- Parameters:

| Parameter name                            | Default | Description                                                                         |
| ----------------------------------------- | ------- | ----------------------------------------------------------------------------------- |
| **file_path**<br />_(\* required)_        |  -      | relative path to audio file from **ROOT_DIR** (`{ROOT_DIR}/{file_path}`) |
| **output_path**<br />_(\* required)_      |  -      | relative path where the modified audio will be saved from **ROOT_DIR** (`{ROOT_DIR}/{output_path}`) |
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


