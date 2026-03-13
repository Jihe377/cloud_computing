import boto3
import time
import json
import os
import urllib.request

s3 = boto3.client('s3')
 
BUCKET_NAME = os.environ['BUCKET_NAME']
PLOTTING_API_URL = os.environ['PLOTTING_API_URL']

def lambda_handler(event, context):
    # 1. Create assignment1.txt with "Empty Assignment 1" (19 bytes)
    s3.put_object(Bucket=BUCKET_NAME, Key='assignment1.txt', Body='Empty Assignment 1')
    time.sleep(2)

    # 2. Update assignment1.txt with "Empty Assignment 2222222222" (28 bytes)
    s3.put_object(Bucket=BUCKET_NAME, Key='assignment1.txt', Body=b'Empty Assignment 2222222222')
    time.sleep(2)

    # 3. Delete assignment1.txt
    s3.delete_object(Bucket=BUCKET_NAME, Key='assignment1.txt')
    time.sleep(2)

    # 4. Create assignment2.txt with "33" (2 bytes)
    s3.put_object(Bucket=BUCKET_NAME, Key='assignment2.txt', Body='33')
    time.sleep(2)

    # 5. Call plotting API
    req = urllib.request.urlopen(PLOTTING_API_URL)
    response_body = req.read().decode('utf-8')
    print(f"Plotting API response: {response_body}")

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Driver completed'})
    }