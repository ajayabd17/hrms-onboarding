import json
import os

import boto3


s3 = boto3.client('s3')
ALLOWED_DOC_TYPES = {'ID_PROOF', 'DEGREE_CERT', 'OFFER_LETTER'}
ALLOWED_CONTENT_TYPES = {
    'application/pdf',
    'image/jpeg',
    'image/png',
    'image/jpg',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
}


def _normalize_content_type(content_type: str) -> str:
    ctype = (content_type or '').strip().lower()
    if ctype == 'image/jpg':
        return 'image/jpeg'
    return ctype


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
            'Access-Control-Allow-Methods': 'OPTIONS,GET'
        },
        'body': json.dumps(body)
    }


def handler(event, _context):
    qs = event.get('queryStringParameters') or {}
    employee_id = qs.get('employee_id')
    doc_type = qs.get('doc_type')
    file_name = qs.get('file_name', 'document.pdf')
    content_type = _normalize_content_type(qs.get('content_type', 'application/pdf'))

    if not employee_id or not doc_type:
        return _resp(400, {'error': 'employee_id and doc_type are required'}, event)
    if doc_type not in ALLOWED_DOC_TYPES:
        return _resp(400, {'error': f'unsupported doc_type: {doc_type}'}, event)
    if content_type not in ALLOWED_CONTENT_TYPES:
        return _resp(
            400,
            {'error': f'unsupported content_type: {content_type}. Allowed: {", ".join(sorted(ALLOWED_CONTENT_TYPES))}'},
            event
        )

    key = f"documents/{employee_id}/{doc_type}/{file_name}"

    upload_url = s3.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': os.environ['DOCS_BUCKET_NAME'],
            'Key': key,
            'ContentType': content_type,
            'ServerSideEncryption': 'AES256'
        },
        ExpiresIn=900,
    )

    return _resp(200, {'upload_url': upload_url, 'key': key})
