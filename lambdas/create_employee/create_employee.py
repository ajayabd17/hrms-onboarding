import json
import os
import uuid
import boto3

dynamodb = boto3.resource('dynamodb')
cognito = boto3.client('cognito-idp')

def handler(event, context):
    try:
        table_name = os.environ.get('EMPLOYEE_TABLE')
        user_pool_id = os.environ.get('USER_POOL_ID')
        table = dynamodb.Table(table_name)
        
        # Handle both API Gateway requests (string body) and direct Lambda tests (dict body)
        raw_body = event.get('body')
        if raw_body is None:
            body = event # Fallback for direct testing in Lambda console
        elif isinstance(raw_body, str):
            body = json.loads(raw_body)
        else:
            body = raw_body
            
        email = body.get('email')
        name = body.get('name')
        department = body.get('department')
        role = body.get('role', 'Employee')
        
        if not email or not name:
            return {'statusCode': 400, 'body': json.dumps({'message': 'Missing email or name'})}
        
        employee_id = str(uuid.uuid4())
        
        # 1. Add to DynamoDB Table
        table.put_item(
            Item={
                'id': employee_id,
                'email': email,
                'name': name,
                'department': department,
                'role': role,
                'status': 'ONBOARDING'
            }
        )
        
        # 2. Add to Cognito
        user_attrs = [
            {'Name': 'email', 'Value': email},
            {'Name': 'email_verified', 'Value': 'true'},
            {'Name': 'given_name', 'Value': name},
            {'Name': 'custom:role', 'Value': role},
            {'Name': 'custom:employee_id', 'Value': employee_id}
        ]
        if department:
            user_attrs.append({'Name': 'custom:department', 'Value': department})
            
        cognito.admin_create_user(
            UserPoolId=user_pool_id,
            Username=email,
            UserAttributes=user_attrs,
            DesiredDeliveryMediums=['EMAIL']
        )
        
        # Assign group (fallback gracefully if group doesn't exist)
        try:
            cognito.admin_add_user_to_group(
                UserPoolId=user_pool_id,
                Username=email,
                GroupName='HR' if role == 'HR' else 'Employee'
            )
        except Exception as e:
            print(f"Warning: Could not add user to group {role}. {e}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True
            },
            'body': json.dumps({'message': 'Employee created successfully', 'employeeId': employee_id})
        }
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'message': str(e)})
        }
