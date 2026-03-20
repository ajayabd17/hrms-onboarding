from datetime import datetime, timezone
import os

import boto3


dynamodb = boto3.resource('dynamodb')


def handler(event, _context):
    employee_id = event['employeeId']
    employee_table = dynamodb.Table(os.environ['EMPLOYEE_TABLE'])
    workflow_table = dynamodb.Table(os.environ['WORKFLOW_TABLE'])

    now = datetime.now(timezone.utc).isoformat()
    employee_table.update_item(
        Key={'employee_id': employee_id},
        UpdateExpression='SET #s = :s, updated_at = :u',
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={':s': 'DAY1_READY', ':u': now}
    )
    workflow_table.update_item(
        Key={'employee_id': employee_id},
        UpdateExpression='SET workflow_status = :s, updated_at = :u',
        ExpressionAttributeValues={':s': 'COMPLETED', ':u': now}
    )
    return {'employee_id': employee_id, 'status': 'DAY1_READY'}
