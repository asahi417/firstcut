"""
Email/PasswordEmail/Password
https://qiita.com/Tokyo/items/263e9ef908fb2cd291bd
"""

import pyrebase
import os

# initialize
serviceAccount = '/Users/aushio/nitro_editor_data/credentials/nitro-test-project-firebase-adminsdk-u2alw-28f8c711bf.json'
config = dict(
    apiKey="AIzaSyA8pt5zhFn-AyN4f8kn9Py_JvtViVmnepM",
    authDomain="nitro-test-project.firebaseapp.com",
    databaseURL="https://nitro-test-project.firebaseio.com",
    storageBucket="nitro-test-project.appspot.com",
    serviceAccount=serviceAccount
)

firebase = pyrebase.initialize_app(config)

# credential
auth = firebase.auth()
user = auth.sign_in_with_email_and_password("asahi1992ushio@gmail.com", "nitro1234")
storage = firebase.storage()

file_path = '/Users/aushio/analysis/nitro_editor/sample_files/sample_0.wav'
file_name = os.path.basename(file_path)

# upload
storage.child(file_name).put(file_path)
url = storage.child(file_name).get_url(token=None)
print(url)

# # download
# output = '/Users/aushio/analysis/nitro_editor/sample_files/sample_0_firebase.wav'
# out = storage.child(file_name).download(output)
# print(out)
#
# # delete
# files = storage.list_files()
# for file in files:
#     print(file, storage.child(file.name).get_url(None))
#     storage.child(file.name).delete(file.name)
