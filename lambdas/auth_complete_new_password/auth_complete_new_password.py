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
    try:
        data = json.loads(event.get('body', '{}')) if 'body' in event else event
        username = (data.get('email') or data.get('username') or '').strip().lower()
        new_password = (data.get('new_password') or '').strip()
        session = (data.get('session') or '').strip()

        if not username or not new_password or not session:
            return _resp(400, {'error': 'email, new_password and session required'}, event)

        inferred_given_name = (username.split('@')[0] if '@' in username else username) or 'User'
        resp = cognito.respond_to_auth_challenge(
            ClientId=os.environ['COGNITO_CLIENT_ID'],
            ChallengeName='NEW_PASSWORD_REQUIRED',
            Session=session,
            ChallengeResponses={
                'USERNAME': username,
                'NEW_PASSWORD': new_password,
                'userAttributes.given_name': inferred_given_name,
            }
        )
    except cognito.exceptions.InvalidPasswordException:
        return _resp(400, {'error': 'new password does not meet policy'}, event)
    except cognito.exceptions.ExpiredCodeException:
        return _resp(401, {'error': 'session expired, login again'}, event)
    except cognito.exceptions.CodeMismatchException:
        return _resp(401, {'error': 'invalid session/challenge, login again'}, event)
    except cognito.exceptions.NotAuthorizedException:
        return _resp(401, {'error': 'challenge failed'}, event)
    except Exception as exc:
        return _resp(500, {'error': f'complete-new-password failed: {str(exc)}'}, event)

    auth = resp.get('AuthenticationResult', {})
    return _resp(200, {
        'access_token': auth.get('AccessToken', ''),
        'id_token': auth.get('IdToken', ''),
        'refresh_token': auth.get('RefreshToken', ''),
        'expires_in': auth.get('ExpiresIn', 3600),
        'token_type': auth.get('TokenType', 'Bearer')
    }, event)

