import json
import os
import boto3

dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    try:
        table_name = os.environ.get('EMPLOYEE_TABLE')
        table = dynamodb.Table(table_name)
        
        raw_body = event.get('body')
        if raw_body is None:
            body = event # Fallback for direct testing
        elif isinstance(raw_body, str):
            body = json.loads(raw_body)
        else:
            body = raw_body
            
        employee_id = body.get('employeeId')
        document_key = body.get('documentKey')
        
        if not employee_id or not document_key:
            return {'statusCode': 400, 'body': json.dumps({'message': 'Missing employeeId or documentKey'})}
            
        # Update database with document
        table.update_item(
            Key={'id': employee_id},
            UpdateExpression='SET document_key = :d, #st = :s',
            ExpressionAttributeNames={'#st': 'status'},
            ExpressionAttributeValues={
                ':d': document_key,
                ':s': 'DOCUMENTS_UPLOADED'
            }
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True
            },
            'body': json.dumps({'message': 'Upload processed successfully!', 'employeeId': employee_id})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }
