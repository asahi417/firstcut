# Firebase setup
Brief introduction to set up firebase.

## Basic procedure
### Create project & bucket
You may first create a project at [firebase](https://console.firebase.google.com) and a storage bucket for the project.

### Get credentials
Go to project page (`https://console.firebase.google.com/project/{project name}/overview`)
1. Go to **Develop > Authentication** and add `user_gmail` and `user_password`.
2. Enable **Sign-in method** of **Email/Password**
3. Go to **Project Overview > Settings** and get `apiKey`, `authDomain`, `databaseURL`, and `storageBucket`.
4. Go to **Project Overview > Settings > Project Settings > Service Accounts > Generate New Private Key** to
 generate service account credential file.
 The file name (a json file) is supposed to set as `serviceAccountCredentials` and the content is used as `FIREBASE_SERVICE_ACOUNT` in the [docker-composer](./docker-compose.yml).
 See the procedure more in detail [here](https://stackoverflow.com/questions/41082171/firebase-permission-denied-with-pyrebase-library/41253388#41253388).  

### Edit docker-compose
Now, you should have all the credentials required in [docker-compose.yml](../docker-compose.yml) file, so 
please fulfil by the credentials 

## Add to composer file
In [docker-composer](./docker-compose.yml), you have to add

```
FIREBASE_APIKEY: ""
FIREBASE_AUTHDOMAIN: ""
FIREBASE_DATABASEURL: ""
FIREBASE_STORAGEBUCKET: ""
FIREBASE_GMAIL: ""
FIREBASE_PASSWORD: ""
FIREBASE_SERVICE_ACOUNT: ""
```

as `args`.
