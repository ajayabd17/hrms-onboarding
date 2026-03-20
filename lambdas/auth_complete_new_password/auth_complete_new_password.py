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
    new_password = (data.get('new_password') or '').strip()
    session = (data.get('session') or '').strip()

    if not username or not new_password or not session:
        return _resp(400, {'error': 'email, new_password and session required'})

    try:
        resp = cognito.respond_to_auth_challenge(
            ClientId=os.environ['COGNITO_CLIENT_ID'],
            ChallengeName='NEW_PASSWORD_REQUIRED',
            Session=session,
            ChallengeResponses={
                'USERNAME': username,
                'NEW_PASSWORD': new_password,
            }
        )
    except cognito.exceptions.NotAuthorizedException:
        return _resp(401, {'error': 'challenge failed'})

    auth = resp.get('AuthenticationResult', {})
    return _resp(200, {
        'access_token': auth.get('AccessToken', ''),
        'id_token': auth.get('IdToken', ''),
        'refresh_token': auth.get('RefreshToken', ''),
        'expires_in': auth.get('ExpiresIn', 3600),
        'token_type': auth.get('TokenType', 'Bearer')
    })
