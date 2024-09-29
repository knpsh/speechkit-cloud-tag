from botocore.exceptions import ClientError
import boto3
import json
import logging
import os
import requests

# Configuration - Logging
logging.getLogger().setLevel(logging.INFO)

# Variables
config = {
    's3_bucket'       : os.environ['S3_BUCKET'],
    's3_prefix'       : os.environ['S3_PREFIX'],
    's3_prefix_log'   : os.environ['S3_PREFIX_LOG'],
    's3_bucket_output': os.environ['S3_BUCKET'],
    's3_prefix_output': os.environ['S3_PREFIX_OUT'],
    's3_key'          : os.environ['S3_KEY'],
    's3_secret'       : os.environ['S3_SECRET'],
    'api_key_secret'  : os.environ['API_SECRET']
}

suffixes = (".mp3", ".wav", ".ogg")

url_operations_api = "https://operation.api.cloud.yandex.net/operations/"
request_header = {'Authorization': 'Api-Key {}'.format(config['api_key_secret'])}

# State - Setting up S3 client
s3 = boto3.client('s3',
    endpoint_url            = 'https://storage.yandexcloud.net',
    aws_access_key_id       = config['s3_key'],
    aws_secret_access_key   = config['s3_secret'] 
)

# Core - Check object in process
def check_processing_objects():
    try:
        object_list = s3.list_objects_v2(Bucket=config['s3_bucket'], Prefix=config['s3_prefix_log'])
        logging.info("Bucket listing successful")
        objects = object_list.get('Contents')

        if not (object_list.get('KeyCount') == 0):
            logging.info("Bucket listing successful")
            objects = object_list.get('Contents')
        else:
            logging.info("Processing directory is empty")
            return None
    except ClientError as e:
        logging.error("Bucket listing failed: {}".format(e))
        return None
    
    for obj in objects:
        key = obj.get('Key')

        if not (key.endswith(".json")):
            continue

        try:
            response = s3.get_object(Bucket=config['s3_bucket'], Key=key)
            logging.info("Object was read: {}".format(key))
        except ClientError as e:
            logging.error("Object read failed: {}".format(e))
            continue
        
        file_content = response['Body'].read().decode('utf-8')
        json_content = json.loads(file_content)

        if not (json_content['id']):
            logging.info("No operation ID in file: {}".format(key))
            continue

        if (json_content['done']):
            logging.info("Already processed: {}".format(json_content['id']))
            continue

        try:
            result = requests.get(url_operations_api+json_content['id'], headers=request_header)
            result.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error("Operation status check failed: {}".format(e))
            continue
        except requests.exceptions.RequestException as e:
            logging.error("Operation status check failed: {}".format(e))
            continue
        else:
            result_data = result.json()

        print(result)
        print(result_data)

        if not (result_data['done']):
            logging.info("Operation in progress: {}".format(result_data['id']))
            continue
        
        result_key = config['s3_prefix_output'] + key[len(config['s3_prefix_log']):]
        result_body = str(json.dumps(result_data, ensure_ascii=False, indent=2))
        print(result_body)

        try:
            s3.put_object(Bucket=config['s3_bucket'], Key=result_key, Body=result_body, ContentType="application/json")
            logging.info("Object process result was written: {}".format(result_key))
        except ClientError as e:
            logging.error("Object result upload failed: {}".format(e))
            continue
        
        if 'response' in result_data and 'chunks' in result_data['response']:
            result_chunks = result_data['response']['chunks']
            result_text_tag1 = ''
            result_text_tag2 = ''
            for chunk in result_chunks:
                if (chunk['channelTag'] == "1"):
                    alternatives = chunk['alternatives']
                    for alternative in alternatives:
                        text = alternative['text']
                        result_text_tag1 += text + '\n'
                if (chunk['channelTag'] == "2"):
                    alternatives = chunk['alternatives']
                    for alternative in alternatives:
                        text = alternative['text']
                        result_text_tag2 += text + '\n'

            result_text_key_tag1 = result_key[:-5]+'.tag1.txt'
            result_text_encoded_tag1 = result_text_tag1.encode('utf-8')

            result_text_key_tag2 = result_key[:-5]+'.tag2.txt'
            result_text_encoded_tag2 = result_text_tag2.encode('utf-8')
        
            try:
                s3.put_object(Bucket=config['s3_bucket'], Key=result_text_key_tag1, Body=result_text_encoded_tag1, ContentType="text/plain")
                logging.info("Object process result was written: {}".format(result_text_key_tag1))
            except ClientError as e:
                logging.error("Object result upload failed: {}".format(e))
                continue
            
            try:
                s3.put_object(Bucket=config['s3_bucket'], Key=result_text_key_tag2, Body=result_text_encoded_tag2, ContentType="text/plain")
                logging.info("Object process result was written: {}".format(result_text_key_tag2))
            except ClientError as e:
                logging.error("Object result upload failed: {}".format(e))
                continue

        body_complete = {
            "done": "true",
            "id": json_content['id']
        }

        try:
            s3.put_object(Bucket=config['s3_bucket'], Key=key, Body=json.dumps(body_complete))
            logging.info("Object process file updated: {}".format(key))
        except ClientError as e:
            logging.error("Object process update failed: {}".format(e))
            continue
            
# Main handler
def handler(event, context):
    check_processing_objects()