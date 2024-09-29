import boto3
import json
import os
import re
from typing import List, Dict
import logging
from collections import Counter

# Configuration - Logging
logging.getLogger().setLevel(logging.INFO)

# Configuration - Global
config = {
    's3_bucket'       : os.environ['S3_BUCKET'],
    's3_bucket_front' : os.environ['S3_BUCKET_FRONT'],
    's3_prefix_output': os.environ['S3_PREFIX_OUT'],
    's3_key'          : os.environ['S3_KEY'],
    's3_secret'       : os.environ['S3_SECRET']
}

# Function - New counter
def count_occurrences(text: str, regex_dict: dict, blocked_list: list) -> list:
    # Remove blocked words
    logging.info("count_ocurrences: {}".format(text))

    # for blocked_word in blocked_list:
    #    text = re.sub(r'\b' + re.escape(blocked_word) + r'\b', '', text, flags=re.IGNORECASE)
    
    for blocked_pattern in blocked_list:
        text = re.sub(r'\b' + blocked_pattern + r'\b', '', text, flags=re.IGNORECASE)
    
    logging.info("count_ocurrences: {}".format(text))

    # Count regex replacements occurrences and remove them from the text
    replacement_counts = {}
    for replacement, pattern in regex_dict.items():
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            replacement_counts[replacement] = len(matches)
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Tokenize the cleaned text and count word occurrences
    tokens = re.findall(r'\b\w+\b', text)
    tokens = [t for t in tokens if len(t) > 2]  # Filter out words with length <= 2
    word_counts = Counter(tokens)

    # Merge the word counts and replacement counts
    word_counts.update(replacement_counts)

    # Flatten
    result = [{"value": word, "count": count} for word, count in word_counts.items()]

    return result

# Function - Find and count phrases
def find_and_count_phrases(text: str, replacement_dict: Dict[str, List[str]]) -> List[Dict[str, int]]:
    result = []  # List to store result dictionaries

    modified_text = text  # Copy of the text to remove phrases from

    for tag, phrases in replacement_dict.items():
        count = 0  # Initialize count to 0 for each tag
        for phrase in phrases:
            matches = re.findall(re.escape(phrase), modified_text, re.IGNORECASE)
            count += len(matches)
            modified_text = re.sub(re.escape(phrase), '', modified_text, flags=re.IGNORECASE)

        if count > 0:  # Only add to result if count is greater than 0
            result.append({"value": tag, "count": count})

    return result, modified_text

# Function - Updating the word count
def update_word_count(text, pre_filled_dict: List[Dict[str, int]]) -> List[Dict[str, int]]:
    result = pre_filled_dict
    # Tokenize the text into words
    words = text.split()
    
    # Count the occurrences of each word in the text
    word_count = Counter(words)
    
    # Update the pre-filled dictionary with the new word counts
    for word, count in word_count.items():
        if(len(word) <= 2):
            continue
        if(word in blocked_dict):
            continue
        result.append({"value": word, "count": count})
    
    return result

# Function - Processing bucket
def process_bucket_files(bucket, replace, block):
    # Initialize the S3 client
    s3 = boto3.client('s3',
        endpoint_url            = 'https://storage.yandexcloud.net',
        aws_access_key_id       = config['s3_key'],
        aws_secret_access_key   = config['s3_secret'] 
    )

    # List objects in the bucket
    response = s3.list_objects(Bucket=bucket)

    # Merged texts
    merged_text_one = ""
    merged_text_two = ""

    # Iterate through each file
    for item in response['Contents']:
        file_name = item['Key']
        local_file = file_name.replace("/", "_")

        # Check if the file is a txt file
        if file_name.endswith('.tag1.txt'):
            text = ""
            # Download the file
            temp_file_name = f"/tmp/{local_file}"
            s3.download_file(bucket, file_name, temp_file_name)

            # Read the file
            with open(temp_file_name, 'r', encoding='utf-8') as f:
                text = f.read()
            
            merged_text_one += text + '\n'

        if file_name.endswith('.tag2.txt'):
            text = ""
            # Download the file
            temp_file_name = f"/tmp/{local_file}"
            s3.download_file(bucket, file_name, temp_file_name)

            # Read the file
            with open(temp_file_name, 'r', encoding='utf-8') as f:
                text = f.read()

            merged_text_two += text + '\n'

    result_list_1, modified_text_1 = find_and_count_phrases(merged_text_one, replace)
    result_list_2, modified_text_2 = find_and_count_phrases(merged_text_two, replace)

    merged_list_1 = update_word_count(modified_text_1, result_list_1)
    merged_list_2 = update_word_count(modified_text_2, result_list_2)

    # Save the results in a JSON file
    result_file_one = "words_tag1.json"
    result_file_two = "words_tag2.json"

    with open(f"/tmp/{result_file_one}", 'w', encoding='utf-8') as f:
        json.dump(merged_list_1, f, ensure_ascii=False)

    
    with open(f"/tmp/{result_file_two}", 'w', encoding='utf-8') as f:
        json.dump(merged_list_2, f, ensure_ascii=False)

    # Upload the JSON file to S3
    s3.upload_file(f"/tmp/{result_file_one}", bucket, result_file_one)
    s3.upload_file(f"/tmp/{result_file_two}", bucket, result_file_two)
    os.remove(f"/tmp/{result_file_one}")
    os.remove(f"/tmp/{result_file_two}")

# Function - Processing bucket new
def process_bucket_files_new(bucket, replace, block):
    # Initialize the S3 client
    s3 = boto3.client('s3',
        endpoint_url            = 'https://storage.yandexcloud.net',
        aws_access_key_id       = config['s3_key'],
        aws_secret_access_key   = config['s3_secret'] 
    )

    # List objects in the bucket
    response = s3.list_objects(Bucket=bucket)

    # Merged texts
    merged_text_one = ""
    merged_text_two = ""

    # Iterate through each file
    for item in response['Contents']:
        file_name = item['Key']
        local_file = file_name.replace("/", "_")

        # Check if the file is a txt file
        if file_name.endswith('.tag1.txt'):
            text = ""
            # Download the file
            temp_file_name = f"/tmp/{local_file}"
            s3.download_file(bucket, file_name, temp_file_name)

            # Read the file
            with open(temp_file_name, 'r', encoding='utf-8') as f:
                text = f.read()
            
            merged_text_one += text + '\n'

        if file_name.endswith('.tag2.txt'):
            text = ""
            # Download the file
            temp_file_name = f"/tmp/{local_file}"
            s3.download_file(bucket, file_name, temp_file_name)

            # Read the file
            with open(temp_file_name, 'r', encoding='utf-8') as f:
                text = f.read()

            merged_text_two += text + '\n'

    result_one = count_occurrences(merged_text_one, replace, block)
    result_two = count_occurrences(merged_text_two, replace, block)

    # Save the results in a JSON file
    result_file_one = "words.tag1.json"
    result_file_two = "words.tag2.json"

    with open(f"/tmp/{result_file_one}", 'w', encoding='utf-8') as f:
        json.dump(result_one, f, ensure_ascii=False)

    
    with open(f"/tmp/{result_file_two}", 'w', encoding='utf-8') as f:
        json.dump(result_two, f, ensure_ascii=False)

    # Upload the JSON file to S3
    s3.upload_file(f"/tmp/{result_file_one}", config['s3_bucket_front'], result_file_one)
    s3.upload_file(f"/tmp/{result_file_two}", config['s3_bucket_front'], result_file_two)
    os.remove(f"/tmp/{result_file_one}")
    os.remove(f"/tmp/{result_file_two}")

# Bucket Name
bucket_name = config['s3_bucket']

# Replacement Dictionary
regexp_dict = {}
blocked_dict = {}  

def handler(event, context):
    process_bucket_files_new(bucket_name, regexp_dict, blocked_dict)
