# Build without Docker
One can manually build with pip and run the script to launch API server.

1. ***Set up environment variables***  
Environment variables:

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
git clone https://github.com/asahi417/firstcut
cd firstcut
pip install -e .
python ./api.py
```
