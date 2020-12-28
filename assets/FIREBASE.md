# Firebase setup
Brief introduction to set up firebase (validated at the moment of 12/28/2020).

## Basic procedure
### Create project & bucket
You may first create a project at [firebase](https://console.firebase.google.com) and create a storage bucket at **Build > Storage**.

### Get credentials
Go to project overview page (`https://console.firebase.google.com/project/{project name}/overview`)
1. Go to **Build > Authentication > Users** and add `user_gmail` and `user_password`.
2. Go to **Build > Authentication > Sign-in method** and enable **Email/Password** sign-in.
3. At **Project Overview**, add new app by clicking **</>** and get `apiKey`, `authDomain`, `databaseURL`, and `storageBucket`, which are shown while adding new app.
4. Go to **Project Overview > Project Settings > Service Accounts** and click **Generate New Private Key** to generate service account credential file.
 The file name (a json file) is `serviceAccountCredentials` and the content is used as `FIREBASE_SERVICE_ACOUNT` in the [docker-composer](./docker-compose.yml).
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
