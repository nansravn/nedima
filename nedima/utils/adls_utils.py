from azure.storage.filedatalake import DataLakeServiceClient
from azure.identity import ClientSecretCredential
import json
import os
from nedima.utils import groundswell as gs

def load_secrets(secrets_path = 'nedima/config/secrets.json'):
    with open(secrets_path, 'r') as fp:
        secrets = json.load(fp)
    return secrets


def initialize_storage_account_ad():
    try:  
        secrets = load_secrets() 

        credential = ClientSecretCredential(secrets['azure']['tenant_id'],\
             secrets['azure']['sp_app_id'], secrets['azure']['sp_secret'])
        service_client = DataLakeServiceClient(account_url="{}://{}.dfs.core.windows.net".format(\
            "https", secrets['azure']['adls_name']), credential=credential)
        return service_client
    
    except Exception as e:
        print(e)
        

def dump_temp_json(input_object, file_name):
    with open(os.path.join('temp',file_name), 'w', encoding='utf-8') as f:
        json.dump(input_object, f, ensure_ascii=False, indent=4)
    return os.path.join('temp',file_name)


def dump_adls_json(dump_dict, latest_tag, fs_client):
    for k in dump_dict.keys():
        temp_path = dump_temp_json(dump_dict[k], "temp_"+k+".json")
        dir_client = fs_client.get_directory_client(os.path.join("tag", "surf", k, gs.get_latest_datetime(latest_tag)))
        json_name = gs.get_latest_datetime(latest_tag, 'time') +  "_"  +  "{:04}".format(len(dump_dict[k])) + ".json"
        file_client = dir_client.create_file(json_name)
        with open(temp_path,'r', encoding="utf-8") as fp:
            file_contents = fp.read()
        file_client.append_data(data=file_contents, offset=0, length=len(file_contents))
        file_client.flush_data(len(file_contents))
        print("[UPLOAD] {} was uploaded to the filesystem {} in the path {}".format(k, \
            file_client.file_system_name, file_client.path_name.replace("\\","/")))


def upload_file_to_directory(service_client):
    try:

        file_system_client = service_client.get_file_system_client(file_system="my-file-system")

        directory_client = file_system_client.get_directory_client("my-directory")
        
        file_client = directory_client.create_file("uploaded-file.txt")
        local_file = open("C:\\file-to-upload.txt",'r')

        file_contents = local_file.read()

        file_client.append_data(data=file_contents, offset=0, length=len(file_contents))

        file_client.flush_data(len(file_contents))

    except Exception as e:
        print(e)