# Firebase setup
Brief introduction to set up firebase (validated at the moment of 12/28/2020).

## Create project & bucket
You may first create a project at [firebase](https://console.firebase.google.com) and create a storage bucket at **Build > Storage**.
The storage url would be `databaseURL` which is required later.

## Get credentials
Go to project overview page (`https://console.firebase.google.com/project/{project name}/overview`)
1. Go to **Build > Authentication > Users** and add `user_gmail` and `user_password`.
2. Go to **Build > Authentication > Sign-in method** and enable **Email/Password** sign-in.
3. At **Project Overview**, add new app by clicking **</>** and get `apiKey`, `authDomain`, and `storageBucket`, which are shown while adding new app.
4. Go to **Project Overview > Project Settings > Service Accounts** and click **Generate New Private Key** to generate service account credential file.
The content in this credential file is used for `FIREBASE_SERVICE_ACOUNT` in the [docker-composer](../docker-compose.yml) config later.

For more info, please take a look [here](https://stackoverflow.com/questions/41082171/firebase-permission-denied-with-pyrebase-library/41253388#41253388).  

## Add to credential to docker-compose config
Now, you have all the credentials required in [docker-compose.yml](../docker-compose.yml) config.
In [docker-composer](./docker-compose.yml), those are set as below.

```
FIREBASE_APIKEY: "apiKey"
FIREBASE_AUTHDOMAIN: "authDomain"
FIREBASE_DATABASEURL: "databaseURL"
FIREBASE_STORAGEBUCKET: ""
FIREBASE_GMAIL: "user_gmail"
FIREBASE_PASSWORD: "user_password"
FIREBASE_SERVICE_ACOUNT: "copy all string in service account credential file and paste here"
```
