import json
import boto3
import base64
import time
from elasticsearch import Elasticsearch, RequestsHttpConnection

def lambda_handler(event, context):
    start_time = time.time()
    photo_id = "Unknown"  # Default value in case photo ID isn't extracted
    bucket = "Unknown"   # Default value in case bucket isn't extracted

    try:
        # Attempt to extract bucket and photo key from the event
        bucket = event['Records'][0]['s3']['bucket']['name']
        photo_key = event['Records'][0]['s3']['object']['key']
        photo_id = photo_key.split('/')[-1]  # Assuming the photo ID is the filename
        print(f"Photo upload detected: {photo_id} with key {photo_key} in bucket {bucket}")
        
        # Initialize boto3 client for Rekognition
        rekognition_client = boto3.client('rekognition')
        s3_client = boto3.client('s3')
        
        # Get the image from S3
        s3_response_time = time.time()
        s3_clientobj = s3_client.get_object(Bucket=bucket, Key=photo_key)
        s3_time_taken = time.time() - s3_response_time
        image_bytes = s3_clientobj['Body'].read()
        decoded_image_content = base64.b64decode(image_bytes)
        print(f"Time taken to retrieve image from S3: {s3_time_taken:.2f} seconds")
        
        # Detect labels in the image using Rekognition
        rekognition_response_time = time.time()
        rekognition_response = rekognition_client.detect_labels(
            Image={'Bytes': decoded_image_content},
            MaxLabels=15,
            MinConfidence=75
        )
        rekognition_time_taken = time.time() - rekognition_response_time
        labels = rekognition_response['Labels']
        custom_labels = [label['Name'] for label in labels]
        print(f"Detected labels for {photo_id}: {custom_labels}")
        print(f"Time taken for Rekognition to detect labels: {rekognition_time_taken:.2f} seconds")
        
        user_labels = s3_clientobj['Metadata'].get('customlabels')
        if user_labels:
            custom_labels.extend(user_labels.split(','))

        # Elasticsearch (OpenSearch Service) host information
        host = "search-photos-uxtdbraw4w3bibpqjm4lypa6x4.us-east-1.es.amazonaws.com"
        es_index = "photos"
        timeStamp = time.time()
        document = {
            'objectKey': photo_key,
            'bucket': bucket,
            'createdTimestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(timeStamp)),
            'labels': custom_labels
        }
        
        # Initialize Elasticsearch client
        es = Elasticsearch(
            hosts=[{'host': host, 'port': 443}],
            http_auth=('******', '**********'),
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )
        
        # Index the document in Elasticsearch
        es_response_time = time.time()
        es.index(index=es_index, body=document)
        es_time_taken = time.time() - es_response_time
        print(f"Document indexed in Elasticsearch, took {es_time_taken:.2f} seconds")

    except Exception as e:
        print(f"Error processing file {photo_id} from bucket {bucket}. Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error processing file {photo_id} from bucket {bucket}. Error: {str(e)}")
        }
    
    total_execution_time = time.time() - start_time
    print(f"Total execution time for processing {photo_id}: {total_execution_time:.2f} seconds")
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'objectKey': photo_key,
            'bucket': bucket,
            'createdTimestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(timeStamp)),
            'labels': custom_labels
        })
    }
