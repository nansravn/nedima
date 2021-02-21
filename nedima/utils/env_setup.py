import json

def load_secrets(secrets_path = 'nedima/config/secrets.json'):
    with open(secrets_path, 'r') as fp:
        secrets = json.load(fp)
    return secrets