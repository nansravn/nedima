from azure.storage.filedatalake import DataLakeServiceClient
from azure.identity import ClientSecretCredential

import json
import os

from nedima.utils import env_setup


def initialize_storage_account_ad(secrets = env_setup.load_secrets()):
    try:  
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


def get_latest_datetime(tag_latest, date_format="%Y/%m/%d"):
    latest_datetime = tag_latest.top_posts[0].upload_time
    if date_format == None:
        return latest_datetime
    elif date_format == 'date':
        return latest_datetime.strftime("%Y%m%d")
    elif date_format == 'time':
        return latest_datetime.strftime("%H%M%S")
    else:
        return latest_datetime.strftime(date_format)


def dump_adls_json(dump_dict, tag_latest, fs_client, flag_print = False,  logging_dict = {}):
    logging_dict['filepath_posts'] = []
    for k in dump_dict.keys():
        temp_path = dump_temp_json(dump_dict[k], "temp_"+k+".json")
        dir_client = fs_client.get_directory_client(os.path.join("tag", "surf", k, get_latest_datetime(tag_latest)))
        json_name = get_latest_datetime(tag_latest, 'time') +  "_"  +  "{:04}".format(len(dump_dict[k])) + ".json"
        file_client = dir_client.create_file(json_name)
        with open(temp_path,'r', encoding="utf-8") as fp:
            file_contents = fp.read()
        file_client.append_data(data=file_contents, offset=0, length=len(file_contents))
        file_client.flush_data(len(file_contents))
        if flag_print:
            print("[UPLOAD] {} was uploaded to the filesystem {} in the path {}".format(k, \
                file_client.file_system_name, file_client.path_name.replace("\\","/")))
        logging_dict['filepath_posts'].append(file_client.path_name.replace("\\","/"))
    
    logging_dict['filepath_posts'] = str(logging_dict['filepath_posts'])
