import json
import os
import logging

import pyrebase

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
__all__ = 'FireBaseConnector'


class FireBaseConnector:
    """ Python client to connect to Fire Base Storage """

    def __init__(self, apiKey, authDomain, databaseURL, storageBucket, gmail, password, serviceAccount):
        """ Python client to connect to Fire Base Storage

         Parameter
        ----------------
        apiKey: Credential
        authDomain: Credential
        databaseURL: Credential
        storageBucket: Credential
        gmail: Credential
        password: Credential
        serviceAccount: Credential
        """
        path = self.write_json_file(serviceAccount, './tmp_firebase_service_account.json')

        self.__firebase = pyrebase.initialize_app(
            dict(apiKey=apiKey,
                 authDomain=authDomain,
                 databaseURL=databaseURL,
                 storageBucket=storageBucket,
                 serviceAccount=path)
        )
        auth = self.__firebase.auth()
        auth.sign_in_with_email_and_password(gmail, password)
        self.__storage = self.__firebase.storage()

    @staticmethod
    def write_json_file(dictionary_obj, path):
        if type(dictionary_obj) is str:
            dictionary_obj = json.loads(dictionary_obj)
        elif type(dictionary_obj) is dict:
            pass
        else:
            return None

        if os.path.exists(path):
            os.system('rm -rf %s' % path)

        with open(path, 'w') as f:
            json.dump(dictionary_obj, f)
        return path

    def get_url(self, file_name: str):
        url = self.__storage.child(file_name).get_url(token=None)
        return url

    def upload(self, file_path: str):
        file_name = os.path.basename(file_path)

        self.__storage.child(file_name).put(file_path)
        url = self.__storage.child(file_name).get_url(token=None)
        return url

    def download(self, file_name, path):
        self.__storage.child(file_name).download(path)

    def remove(self, file_name: str = None):
        if file_name:
            self.__storage.child(file_name).delete(file_name)
            return [file_name]
        else:
            files = self.__storage.list_files()
            removed_list = []
            for file in files:
                self.__storage.child(file.name).delete(file.name)
                removed_list.append(file.name)
            return removed_list

    @property
    def list_files(self):
        return self.__storage.list_files()

