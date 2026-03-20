import json
import os
import boto3

s3_client = boto3.client('s3')

def handler(event, context):
    try:
        bucket_name = os.environ.get('DOCS_BUCKET_NAME')
        query_params = event.get('queryStringParameters')
        if query_params is None:
            query_params = event # Fallback for direct Lambda console testing
            
        filename = query_params.get('filename', 'document.pdf')
        employee_id = query_params.get('employeeId', 'unknown')
        
        object_key = f"uploads/{employee_id}/{filename}"
        
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket_name,
                'Key': object_key,
                'ContentType': 'application/pdf'
            },
            ExpiresIn=3600
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True
            },
            'body': json.dumps({'uploadUrl': presigned_url, 'key': object_key})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }
