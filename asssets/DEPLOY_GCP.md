# Register docker image to container registry
Enable docker registry [here](https://console.cloud.google.com/apis/library/containerregistry.googleapis.com?project=nitro-test-project).

Build docker image
```
$ docker-compose -f docker-compose.yml up
$ docker images

REPOSITORY                      TAG                 IMAGE ID            CREATED             SIZE
nitro_editor_api                latest              7fa84829228d        9 minutes ago       1.05GB       
```

Tag gcp project
```
$ export GCP_PROJECT_ID=nitro-test-project
$ export GCP_IMAGE_ID=7fa84829228d
$ docker tag nitro_editor_api gcr.io/${GCP_PROJECT_ID}/nitro_editor_api
$ docker image ls

REPOSITORY                                   TAG                 IMAGE ID            CREATED             SIZE
nitro_editor_api                             latest              7fa84829228d        13 minutes ago      1.05GB
gcr.io/nitro-test-project/nitro_editor_api   latest              7fa84829228d        13 minutes ago      1.05GB
```

Login to gcloud project
```
$ export GCLOUD_PROJECT=nitro-test-project
$ gcloud auth application-default login
$ gcloud auth login
```

Upload on gcp project

```
$ gcloud docker -- push gcr.io/${GCP_PROJECT_ID}/nitro_editor_api
```

Check if the images has been deployed from [console](https://console.cloud.google.com/gcr/images/nitro-test-project?project=nitro-test-project). 