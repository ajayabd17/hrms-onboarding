import json
import os

import boto3


cognito = boto3.client('cognito-idp')


def _resp(code: int, body: dict):
    return {
        'statusCode': code,
        'headers': {
            'Access-Control-Allow-Origin': os.environ.get('ALLOWED_ORIGIN', '*'),
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'OPTIONS,POST'
        },
        'body': json.dumps(body)
    }


def handler(event, _context):
    data = json.loads(event.get('body', '{}')) if 'body' in event else event
    username = (data.get('email') or data.get('username') or '').strip().lower()
    password = (data.get('password') or '').strip()

    if not username or not password:
        return _resp(400, {'error': 'email and password required'})

    try:
        resp = cognito.initiate_auth(
            ClientId=os.environ['COGNITO_CLIENT_ID'],
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password,
            }
        )
    except cognito.exceptions.NotAuthorizedException:
        return _resp(401, {'error': 'invalid credentials'})
    except cognito.exceptions.UserNotFoundException:
        return _resp(404, {'error': 'user not found'})

    if resp.get('ChallengeName') == 'NEW_PASSWORD_REQUIRED':
        return _resp(200, {
            'challenge': 'NEW_PASSWORD_REQUIRED',
            'session': resp.get('Session', ''),
            'username': username,
        })

    auth = resp.get('AuthenticationResult', {})
    return _resp(200, {
        'access_token': auth.get('AccessToken', ''),
        'id_token': auth.get('IdToken', ''),
        'refresh_token': auth.get('RefreshToken', ''),
        'expires_in': auth.get('ExpiresIn', 3600),
        'token_type': auth.get('TokenType', 'Bearer')
    })
