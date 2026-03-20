import json
import os

import boto3


cognito = boto3.client('cognito-idp')


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


def handler(event, _context):
    data = json.loads(event.get('body', '{}')) if 'body' in event else event
    username = (data.get('email') or data.get('username') or '').strip().lower()
    password = (data.get('password') or '').strip()

    if not username or not password:
        return _resp(400, {'error': 'email and password required'}, event)

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
        return _resp(401, {'error': 'invalid credentials'}, event)
    except cognito.exceptions.UserNotFoundException:
        return _resp(404, {'error': 'user not found'}, event)

    if resp.get('ChallengeName') == 'NEW_PASSWORD_REQUIRED':
        return _resp(200, {
            'challenge': 'NEW_PASSWORD_REQUIRED',
            'session': resp.get('Session', ''),
            'username': username,
        }, event)

    auth = resp.get('AuthenticationResult', {})
    return _resp(200, {
        'access_token': auth.get('AccessToken', ''),
        'id_token': auth.get('IdToken', ''),
        'refresh_token': auth.get('RefreshToken', ''),
        'expires_in': auth.get('ExpiresIn', 3600),
        'token_type': auth.get('TokenType', 'Bearer')
    }, event)
