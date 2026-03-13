import boto3
from boto3.dynamodb.conditions import Key
import time
import json
import io
import os
from datetime import datetime, timezone
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

TABLE_NAME = os.environ['TABLE_NAME']
BUCKET_NAME = os.environ['BUCKET_NAME']
GSI_NAME = os.environ['GSI_NAME']
 
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    now = int(time.time())
    start = now - 10
    
    # ---- Query last 10 seconds for TestBucket ----
    response = table.query(
        KeyConditionExpression= Key('bucket_name').eq(BUCKET_NAME) & Key('timestamp').between(start, now)
    )
    items = response.get('Items', [])
    
    timestamps = []
    sizes = []
    for item in sorted(items, key=lambda x: x['timestamp']):
        timestamps.append(datetime.fromtimestamp(int(item['timestamp']), tz=timezone.utc))
        sizes.append(int(item['total_size']))
    
    # ---- Query global max size across ALL buckets ----
    gsi_response = table.query(
        IndexName=GSI_NAME,
        KeyConditionExpression=Key('record_type').eq('size_record'),
        ScanIndexForward=False,  # descending by total_size
        Limit=1,
    )
    gsi_items = gsi_response.get('Items', [])
    max_size = int(gsi_items[0]['total_size']) if gsi_items else 0


    # ---- Plot ----
    fig, ax = plt.subplots(figsize=(10, 5))
    
    if timestamps and sizes:
        ax.plot(timestamps, sizes, marker='o', label='Bucket Size (last 10s)', color='blue')
    else:
        ax.text(0.5, 0.5, 'No data in last 10 seconds',
                ha='center', va='center', transform=ax.transAxes)
    
    # Max size line
    ax.axhline(y=max_size, color='red', linestyle='--', label=f'Max Ever Size: {max_size} bytes')
    
    ax.set_xlabel('Timestamp (UTC)')
    ax.set_ylabel('Total Size (bytes)')
    ax.set_title(f'S3 Bucket Size Over Time - {BUCKET_NAME}')
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    fig.autofmt_xdate()
    plt.tight_layout()
    
    # Save plot to S3
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key='plot',
        Body=buf.getvalue(),
        ContentType='image/png'
    )
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'message': 'Plot generated and saved to S3', 'max_size': max_size})
    }