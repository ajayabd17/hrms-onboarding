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


def handler(_event, _context):
    employee_table = dynamodb.Table(os.environ['EMPLOYEE_TABLE'])
    stage_table = dynamodb.Table(os.environ['STAGE_STATUS_TABLE'])

    employees = employee_table.scan().get('Items', [])
    result = []

    for emp in employees:
        employee_id = emp.get('employee_id')
        if not employee_id:
            continue
        stage_items = stage_table.query(
            KeyConditionExpression=Key('employee_id').eq(employee_id)
        ).get('Items', [])

        completed = sum(1 for s in stage_items if s.get('status') == 'COMPLETE')
        in_progress = next((s.get('stage_name') for s in stage_items if s.get('status') == 'IN_PROGRESS'), None)

        result.append({
            'employee_id': employee_id,
            'full_name': emp.get('full_name'),
            'email': emp.get('email'),
            'department': emp.get('department'),
            'status': emp.get('status'),
            'completed_stages': completed,
            'active_stage': in_progress or 'PENDING',
        })

    return _resp(200, {'employees': result})
