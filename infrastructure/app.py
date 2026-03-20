#!/usr/bin/env python3
import aws_cdk as cdk
import os
from aws_cdk import aws_cognito as cognito

from stacks.storage_stack import StorageStack
from stacks.compute_stack import ComputeStack
from stacks.messaging_stack import MessagingStack
from stacks.orchestration_stack import OrchestrationStack
from stacks.api_stack import ApiStack

app = cdk.App()

env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "ap-south-1")
)

frontend_origin = os.environ.get("HRMS_FRONTEND_ORIGIN", "https://dhkkwtcsx3bir.cloudfront.net")

storage = StorageStack(app, "HrmsStorageStack", frontend_origin=frontend_origin, env=env)

existing_user_pool_id = os.environ.get("HRMS_EXISTING_USER_POOL_ID", "ap-south-1_qWhBjVn8Z")
existing_user_pool_client_id = os.environ.get("HRMS_EXISTING_USER_POOL_CLIENT_ID", "hp08mpeaq49rmj1l0fo36gmdq")
identity_ref = cdk.Stack(app, "HrmsIdentityRefStack", env=env)
identity = cognito.UserPool.from_user_pool_id(identity_ref, "HrmsImportedUserPool", user_pool_id=existing_user_pool_id)

messaging = MessagingStack(app, "HrmsMessagingStack", env=env)

compute = ComputeStack(
    app, "HrmsComputeStack",
    employee_table=storage.employee_table,
    workflow_table=storage.workflow_table,
    stage_status_table=storage.stage_status_table,
    document_table=storage.document_table,
    user_pool=identity,
    user_pool_client_id=existing_user_pool_client_id,
    docs_bucket=storage.docs_bucket,
    hr_topic=messaging.hr_topic,
    frontend_origin=frontend_origin,
    env=env
)
compute.bind_reminder_lambda()

orchestration = OrchestrationStack(
    app,
    "HrmsOrchestrationStack",
    stage_executor_fn=compute.stage_executor_fn,
    finalize_onboarding_fn=compute.finalize_onboarding_fn,
    hr_topic=messaging.hr_topic,
    env=env
)

api = ApiStack(
    app,
    "HrmsApiStack",
    user_pool=identity,
    auth_login_fn=compute.auth_login_fn,
    auth_complete_new_password_fn=compute.auth_complete_new_password_fn,
    create_employee_fn=compute.create_employee_fn,
    get_upload_url_fn=compute.get_upload_url_fn,
    progress_api_fn=compute.progress_api_fn,
    complete_stage_fn=compute.complete_stage_fn,
    list_employees_fn=compute.list_employees_fn,
    frontend_origin=frontend_origin,
    env=env
)

app.synth()
