import json
import os
import uuid
from datetime import datetime, timezone

import boto3


dynamodb = boto3.resource('dynamodb')
cognito = boto3.client('cognito-idp')
ses = boto3.client('ses')
sfn = boto3.client('stepfunctions')


def _resp(code: int, body: dict):
    return {
        'statusCode': code,
        'headers': {
            'Access-Control-Allow-Origin': os.environ.get('ALLOWED_ORIGIN', '*'),
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'OPTIONS,GET,POST'
        },
        'body': json.dumps(body)
    }


def handler(event, context):
    payload = json.loads(event.get('body', '{}')) if 'body' in event else event
    required = ['email', 'full_name', 'department', 'role', 'manager_id', 'joining_date', 'employment_type']
    missing = [k for k in required if not payload.get(k)]
    if missing:
        return _resp(400, {'error': f'missing fields: {", ".join(missing)}'})

    employee_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    employee_table = dynamodb.Table(os.environ['EMPLOYEE_TABLE'])
    workflow_table = dynamodb.Table(os.environ['WORKFLOW_TABLE'])

    employee_table.put_item(Item={
        'employee_id': employee_id,
        'email': payload['email'].strip().lower(),
        'full_name': payload['full_name'],
        'department': payload['department'],
        'role': payload['role'],
        'manager_id': payload['manager_id'],
        'joining_date': payload['joining_date'],
        'employment_type': payload['employment_type'],
        'status': 'ONBOARDING',
        'created_at': now,
        'updated_at': now
    })

    temp_password = os.environ.get('TEMP_PASSWORD', 'TempPassw0rd!')
    cognito.admin_create_user(
        UserPoolId=os.environ['USER_POOL_ID'],
        Username=payload['email'].strip().lower(),
        TemporaryPassword=temp_password,
        MessageAction='SUPPRESS',
        UserAttributes=[
            {'Name': 'email', 'Value': payload['email'].strip().lower()},
            {'Name': 'email_verified', 'Value': 'true'},
            {'Name': 'given_name', 'Value': payload['full_name']},
            {'Name': 'custom:employee_id', 'Value': employee_id},
            {'Name': 'custom:department', 'Value': payload['department']},
            {'Name': 'custom:role', 'Value': payload['role']},
            {'Name': 'custom:manager', 'Value': payload['manager_id']},
            {'Name': 'custom:joining_date', 'Value': payload['joining_date']},
            {'Name': 'custom:employment_type', 'Value': payload['employment_type']},
        ]
    )

    portal_url = os.environ.get('PORTAL_URL', 'http://localhost:5173')
    if os.environ.get('SES_FROM_EMAIL'):
        ses.send_email(
            Source=os.environ['SES_FROM_EMAIL'],
            Destination={'ToAddresses': [payload['email']]},
            Message={
                'Subject': {'Data': 'Welcome to onboarding portal'},
                'Body': {
                    'Text': {
                        'Data': (
                            f"Hi {payload['full_name']},\n\n"
                            f"Use this temporary password to log in: {temp_password}\n"
                            f"Portal: {portal_url}\n"
                        )
                    }
                }
            }
        )

    execution_arn = None
    state_machine_arn = os.environ.get('STATE_MACHINE_ARN')
    if not state_machine_arn and os.environ.get('STATE_MACHINE_NAME'):
        fn_arn = context.invoked_function_arn
        region = fn_arn.split(':')[3]
        account_id = fn_arn.split(':')[4]
        state_machine_arn = f"arn:aws:states:{region}:{account_id}:stateMachine:{os.environ['STATE_MACHINE_NAME']}"

    if state_machine_arn:
        exec_resp = sfn.start_execution(
            stateMachineArn=state_machine_arn,
            name=f"onboarding-{employee_id}",
            input=json.dumps({'employeeId': employee_id, 'email': payload['email'].strip().lower()})
        )
        execution_arn = exec_resp.get('executionArn')

    workflow_table.put_item(Item={
        'employee_id': employee_id,
        'workflow_status': 'STARTED',
        'execution_arn': execution_arn or 'PENDING_BINDING',
        'created_at': now,
        'updated_at': now,
    })

    return _resp(200, {'employee_id': employee_id, 'execution_arn': execution_arn})
