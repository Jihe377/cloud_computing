import boto3
import os
import json
import time

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
 
TABLE_NAME = os.environ['TABLE_NAME']
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    # Get bucket name from the S3 event
    sns_message = json.loads(event['Records'][0]['Sns']['Message'])
    bucket_name = sns_message['Records'][0]['s3']['bucket']['name']
    
    # Compute total size and count of all objects
    total_size = 0
    total_count = 0

    # Actually not necessary for this assignment, since the dataset is small 
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket_name)
    
    for page in pages:
        for obj in page.get('Contents', []):
            total_size += obj['Size']
            total_count += 1
    
    # Write to DynamoDB
    timestamp = int(time.time())
    
    table.put_item(Item={
        'bucket_name': bucket_name,
        'timestamp': timestamp,
        'total_size': total_size,
        'object_count': total_count,
        'record_type': 'size_record',  
    })
    
    # print(f"Recorded: bucket={bucket_name}, size={total_size}, count={total_count}, time={timestamp}")
    
    return {
        'statusCode': 200,
        'body': json.dumps({'bucket': bucket_name, 'total_size': total_size})
    }