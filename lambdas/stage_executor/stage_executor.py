import json
import os
from datetime import datetime, timezone

import boto3


dynamodb = boto3.resource('dynamodb')
events = boto3.client('events')


def handler(event, _context):
    stage = event['stage']
    employee_id = event['employeeId']
    task_token = event['taskToken']
    now = datetime.now(timezone.utc).isoformat()

    employee_table = dynamodb.Table(os.environ['EMPLOYEE_TABLE'])
    stage_table = dynamodb.Table(os.environ['STAGE_STATUS_TABLE'])

    employee_table.update_item(
        Key={'employee_id': employee_id},
        UpdateExpression='SET #token_attr = :token, updated_at = :u',
        ExpressionAttributeNames={'#token_attr': f"{stage.lower()}_task_token"},
        ExpressionAttributeValues={':token': task_token, ':u': now}
    )

    stage_table.put_item(Item={
        'employee_id': employee_id,
        'stage_name': stage,
        'status': 'IN_PROGRESS',
        'started_at': now,
        'reminder_count': 0,
        'last_reminder_at': ''
    })

    if os.environ.get('REMINDER_LAMBDA_ARN'):
        rule_name = f"hrms-{employee_id[:8]}-{stage.lower()}"
        events.put_rule(Name=rule_name, ScheduleExpression='rate(24 hours)', State='ENABLED')
        events.put_targets(
            Rule=rule_name,
            Targets=[{
                'Id': 'ReminderTarget',
                'Arn': os.environ['REMINDER_LAMBDA_ARN'],
                'Input': json.dumps({'employeeId': employee_id, 'stage': stage, 'ruleName': rule_name})
            }]
        )

    return {'status': 'WAITING', 'stage': stage, 'employee_id': employee_id}
