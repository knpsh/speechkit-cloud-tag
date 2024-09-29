from botocore.exceptions import ClientError
import boto3
import os
import json
import requests
import logging

# Global - Logging
logging.getLogger().setLevel(logging.INFO)

# Global - Variables
config = {
    's3_bucket'       : os.environ['S3_BUCKET'],
    's3_prefix'       : os.environ['S3_PREFIX'],
    's3_prefix_log'   : os.environ['S3_PREFIX_LOG'],
    's3_bucket_output': os.environ['S3_BUCKET'],
    's3_prefix_output': os.environ['S3_PREFIX_OUT'],
    's3_key'          : os.environ['S3_KEY'],
    's3_secret'       : os.environ['S3_SECRET'],
    'api_key_secret'  : os.environ['API_SECRET'],
}

url_transcribe_api  = "https://transcribe.api.cloud.yandex.net/speech/stt/v2/longRunningRecognize"
request_header      = {'Authorization': 'Api-Key {}'.format(config['api_key_secret'])}

# STT - Setting up S3 client
s3 = boto3.client('s3',
    endpoint_url            = 'https://storage.yandexcloud.net',
    aws_access_key_id       = config['s3_key'],
    aws_secret_access_key   = config['s3_secret'] 
)

# STT - Create recognition task
def create_recognition_task(url, file_type, lang = 'ru-RU'):
    if (file_type == "mp3"):
        request_body = {
            "config": {
                "specification": {
                    "audioEncoding": "MP3",
                    "languageCode": lang
                }
            },
            "audio": {
                "uri": url
            }
        }
    elif (file_type == "wav"):
        request_body = {
            "config": {
                "specification": {
                    "audioEncoding": "LINEAR16_PCM",
                    "model": "general:rc",
                    "sampleRateHertz": "48000", # keep in check
                    "languageCode": lang,
                    "audioChannelCount": "2",
                    "rawResults": "true"
                }
            },
            "audio": {
                "uri": url
            }
        }
    elif (file_type == "ogg"):
        request_body = {
            "config": {
                "specification": {
                    "audioEncoding": "OGG_OPUS",
                    "languageCode": lang
                }
            },
            "audio": {
                "uri": url
            }
        }
    
    try:
        response = requests.post(url_transcribe_api, headers=request_header, json=request_body)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.error("Transcribe request failed: {}".format(e))
    except requests.exceptions.RequestException as e:
        logging.error("Transcribe request failed: {}".format(e))
    else:
        request_data = response.json()
    
        if(request_data['id']):
            logging.info("Operation {}".format(request_data['id']))
            logging.info("Operation has been created for {}".format(url))
            return request_data
        else: 
            logging.error("Operation ID is missing in the response")
            return {"Status": "None"}

# STT - Write process status
def write_process_status(key, data):
    json_data = json.dumps(data)
    try:
        s3.put_object(Bucket=config['s3_bucket'], Key=key, Body=json_data)
        logging.info("Object process status was written: {}".format(key))
        return True
    except ClientError as e:
        logging.error("Object upload failed: {}".format(e))
        return None

# STT - Send
def send_to_transcribe(url):
    file_type = "wav"
    result = create_recognition_task(url, file_type)
    if not (result == None):
        key_process = config['s3_prefix_log'] + '/' + result['id'] + ".json"
        write_process_status(key_process, result)
        return True
    else:
        return False

# Preflight
def preflight_response(event):
    print("Preflight request")
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Max-Age': '300'
        },
        'body': event['body']
    }

# Main handler
def handler(event, context):
    if event['httpMethod'] == 'OPTIONS':
        return preflight_response(event)
    
    logging.info("Handler start")

    try:
        body = json.loads(event['body'])
    except json.JSONDecodeError as e:
        print("Error decoding JSON:", e)

    logging.info("Body: {}".format(body))
    
    if(body['url']):
        url = body['url']
        logging.info("url: {}".format(url))
    else:
        return {
            'statusCode': 404,
            'headers:': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST,GET,OPTIONS, PUT, DELETE',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Max-Age': '300'
            },
            'body': "No valid url provided."
        }

    response = send_to_transcribe(url)
    logging.info("{}".format(response))

    return {
        'statusCode': 200,
        'headers:': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST,GET,OPTIONS, PUT, DELETE',
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Max-Age': '300'
        },
        'body': response
    }