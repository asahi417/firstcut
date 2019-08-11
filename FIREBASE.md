# Firebase setup
Brief introduction to set up firebase.

## Basic procedure
### Create project & bucket
If you don't have any projects for nitro-editor, create a project of [firebase](https://console.firebase.google.com) and
a storage bucket for the project.

### Get credentials
Go to project page (`https://console.firebase.google.com/project/{project name}/overview`)
1. Go to **Develop > Authentication** and add `user_gmail` and `user_password`.
2. Enable **Sign-in method** of **Email/Password**
3. Go to **Project Overview > Settings** and get `apiKey`, `authDomain`, `databaseURL`, and `storageBucket`.
4. Go to **Project Overview > Settings > Project Settings > Service Accounts > Generate New Private Key** to
 generate service account credential file.
 The file name (a json file) is supposed to set as `serviceAccountCredentials` and the path to the directory where 
 the credential located, is `path-to-credentials` (so the absolute path to the credential becomes `path-to-credentials/serviceAccountCredentials`).
 See the procedure more in detail [here](https://stackoverflow.com/questions/41082171/firebase-permission-denied-with-pyrebase-library/41253388#41253388).  

### Edit docker-compose
Now, you should have all the credentials required in [docker-compose.yml](./docker-compose.yml) file, so 
please fulfil by the credentials 

