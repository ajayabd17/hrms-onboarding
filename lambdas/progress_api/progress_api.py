import json
import os

import boto3
from boto3.dynamodb.conditions import Key


dynamodb = boto3.resource('dynamodb')


def _resp(code: int, body: dict):
    return {
        'statusCode': code,
        'headers': {
            'Access-Control-Allow-Origin': os.environ.get('ALLOWED_ORIGIN', '*'),
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'OPTIONS,GET'
        },
        'body': json.dumps(body)
    }


def handler(event, _context):
    employee_id = (event.get('pathParameters') or {}).get('employee_id') or (event.get('queryStringParameters') or {}).get('employee_id')
    if not employee_id:
        return _resp(400, {'error': 'employee_id is required'})

    stage_table = dynamodb.Table(os.environ['STAGE_STATUS_TABLE'])
    workflow_table = dynamodb.Table(os.environ['WORKFLOW_TABLE'])

    stages = stage_table.query(KeyConditionExpression=Key('employee_id').eq(employee_id)).get('Items', [])
    wf = workflow_table.get_item(Key={'employee_id': employee_id}).get('Item', {})

    return _resp(200, {
        'employee_id': employee_id,
        'workflow_status': wf.get('workflow_status', 'UNKNOWN'),
        'execution_arn': wf.get('execution_arn'),
        'stages': sorted(stages, key=lambda x: x.get('stage_name', ''))
    })
