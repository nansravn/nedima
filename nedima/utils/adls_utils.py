from azure.storage.filedatalake import DataLakeServiceClient
from azure.identity import ClientSecretCredential
import json

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