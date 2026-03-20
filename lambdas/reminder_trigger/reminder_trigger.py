import os
from datetime import datetime, timedelta, timezone

import boto3


dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')


def handler(event, _context):
    employee_id = event['employeeId']
    stage = event['stage']

    stage_table = dynamodb.Table(os.environ['STAGE_STATUS_TABLE'])
    employee_table = dynamodb.Table(os.environ['EMPLOYEE_TABLE'])

    stage_item = stage_table.get_item(Key={'employee_id': employee_id, 'stage_name': stage}).get('Item', {})
    if stage_item.get('status') == 'COMPLETE':
        return {'skipped': True, 'reason': 'already complete'}

    now = datetime.now(timezone.utc)
    last_sent = stage_item.get('last_reminder_at')
    if last_sent:
        try:
            last_dt = datetime.fromisoformat(last_sent)
            if now - last_dt < timedelta(hours=23):
                return {'skipped': True, 'reason': 'recently sent'}
        except ValueError:
            pass

    employee = employee_table.get_item(Key={'employee_id': employee_id}).get('Item', {})
    email = employee.get('email')
    if email and os.environ.get('SES_FROM_EMAIL'):
        ses.send_email(
            Source=os.environ['SES_FROM_EMAIL'],
            Destination={'ToAddresses': [email]},
            Message={
                'Subject': {'Data': f'Reminder: complete onboarding stage {stage}'},
                'Body': {'Text': {'Data': f'Please complete stage {stage} for employee id {employee_id}.'}}
            }
        )

    stage_table.update_item(
        Key={'employee_id': employee_id, 'stage_name': stage},
        UpdateExpression='SET reminder_count = if_not_exists(reminder_count, :zero) + :inc, last_reminder_at = :now',
        ExpressionAttributeValues={':zero': 0, ':inc': 1, ':now': now.isoformat()}
    )

    return {'sent': True, 'employee_id': employee_id, 'stage': stage}
