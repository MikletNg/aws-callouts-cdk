import os
import boto3
import json

s3 = boto3.client('s3')


def lambda_handler(event, context):
    print(event)
    key = event
    s3.download_file(os.environ['S3Bucket'], f"task/{key}", '/tmp/call.json')
    receiver = json.loads(open('/tmp/call.json', 'r').read())
    return receiver
