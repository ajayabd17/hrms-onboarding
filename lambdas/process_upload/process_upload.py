import json
import os
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key


dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
sfn = boto3.client('stepfunctions')
sns = boto3.client('sns')
events = boto3.client('events')

REQUIRED_DOCS = {'ID_PROOF', 'DEGREE_CERT', 'OFFER_LETTER'}
ALLOWED_TYPES = {
    'application/pdf',
    'image/jpeg',
    'image/png',
    'image/jpg',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
}
MAX_BYTES = 10 * 1024 * 1024


def _normalize_content_type(content_type: str) -> str:
    ctype = (content_type or '').strip().lower()
    if ctype == 'image/jpg':
        return 'image/jpeg'
    return ctype


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
    for record in event.get('Records', []):
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        size = int(record['s3']['object'].get('size', 0))

        parts = key.split('/')
        if len(parts) < 4:
            continue
        employee_id = parts[1]
        doc_type = parts[2]

        doc_table = dynamodb.Table(os.environ['DOCUMENT_TABLE'])
        stage_table = dynamodb.Table(os.environ['STAGE_STATUS_TABLE'])
        employee_table = dynamodb.Table(os.environ['EMPLOYEE_TABLE'])

        status = 'VERIFIED'
        reason = ''
        if size > MAX_BYTES:
            status = 'REJECTED'
            reason = 'FILE_TOO_LARGE'
        else:
            head = s3.head_object(Bucket=bucket, Key=key)
            content_type = _normalize_content_type(head.get('ContentType', ''))
            if content_type not in ALLOWED_TYPES:
                status = 'REJECTED'
                reason = f'UNSUPPORTED_TYPE:{content_type or "unknown"}'

        now = datetime.now(timezone.utc).isoformat()
        doc_table.put_item(Item={
            'employee_id': employee_id,
            'doc_type': doc_type,
            's3_key': key,
            'status': status,
            'reason': reason,
            'updated_at': now
        })

        docs = doc_table.query(KeyConditionExpression=Key('employee_id').eq(employee_id)).get('Items', [])
        verified = {d['doc_type'] for d in docs if d.get('status') == 'VERIFIED'}

        if REQUIRED_DOCS.issubset(verified):
            stage_table.update_item(
                Key={'employee_id': employee_id, 'stage_name': 'DOC_COLLECTION'},
                UpdateExpression='SET #s = :s, completed_at = :t',
                ExpressionAttributeNames={'#s': 'status'},
                ExpressionAttributeValues={':s': 'COMPLETE', ':t': now}
            )
            emp = employee_table.get_item(Key={'employee_id': employee_id}).get('Item', {})
            task_token = emp.get('doc_collection_task_token')
            if task_token:
                sfn.send_task_success(taskToken=task_token, output=json.dumps({'employeeId': employee_id, 'stage': 'DOC_COLLECTION'}))
            _remove_rule(f"hrms-{employee_id[:8]}-doc_collection")
            if os.environ.get('HR_TOPIC_ARN'):
                sns.publish(
                    TopicArn=os.environ['HR_TOPIC_ARN'],
                    Subject='Documents verified',
                    Message=f'All required documents verified for {employee_id}'
                )
