import json
import os
from datetime import datetime, timezone

import boto3


dynamodb = boto3.resource('dynamodb')
sfn = boto3.client('stepfunctions')
events = boto3.client('events')


def _cors_origin(event):
    headers = (event or {}).get('headers') or {}
    origin = headers.get('origin') or headers.get('Origin')
    allowed = {o.strip() for o in os.environ.get('ALLOWED_ORIGINS', '').split(',') if o.strip()}
    if origin and origin in allowed:
        return origin
    return os.environ.get('ALLOWED_ORIGIN', '*')


def _resp(code: int, body: dict, event=None):
    return {
        'statusCode': code,
        'headers': {
            'Access-Control-Allow-Origin': _cors_origin(event),
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'OPTIONS,POST'
        },
        'body': json.dumps(body)
    }


def _remove_rule(rule_name: str):
    try:
        events.remove_targets(Rule=rule_name, Ids=['ReminderTarget'])
    except Exception:
        pass
    try:
        events.delete_rule(Name=rule_name)
    except Exception:
        pass


def handler(event, _context):
    employee_id = (event.get('pathParameters') or {}).get('employee_id')
    data = json.loads(event.get('body', '{}')) if 'body' in event else event
    stage = data.get('stage')
    if not employee_id or not stage:
        return _resp(400, {'error': 'employee_id and stage required'}, event)

    stage_table = dynamodb.Table(os.environ['STAGE_STATUS_TABLE'])
    employee_table = dynamodb.Table(os.environ['EMPLOYEE_TABLE'])

    emp = employee_table.get_item(Key={'employee_id': employee_id}).get('Item', {})
    token = emp.get(f'{stage.lower()}_task_token')
    if not token:
        return _resp(404, {'error': f'no task token for stage {stage}'}, event)

    sfn.send_task_success(taskToken=token, output=json.dumps({'employeeId': employee_id, 'stage': stage}))

    stage_table.update_item(
        Key={'employee_id': employee_id, 'stage_name': stage},
        UpdateExpression='SET #s = :s, completed_at = :t',
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={':s': 'COMPLETE', ':t': datetime.now(timezone.utc).isoformat()}
    )

    _remove_rule(f"hrms-{employee_id[:8]}-{stage.lower()}")

    return _resp(200, {'ok': True, 'employee_id': employee_id, 'stage': stage}, event)
