#!/usr/bin/env python3
import aws_cdk as cdk
import os

from stacks.storage_stack import StorageStack
from stacks.identity_stack import IdentityStack
from stacks.compute_stack import ComputeStack
from stacks.api_stack import ApiStack

app = cdk.App()

env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "ap-south-1")
)

# 1. Storage
storage = StorageStack(app, "HrmsStorageStack", env=env)

# 2. Identity
identity = IdentityStack(app, "HrmsIdentityStack", env=env)

# 3. Compute
compute = ComputeStack(
    app, "HrmsComputeStack",
    employee_table=storage.employee_table,
    user_pool=identity.user_pool,
    docs_bucket_name=storage.docs_bucket.bucket_name,
    env=env
)

# 4. API (Exposes Compute to Internet using Identity for Authn)
api = ApiStack(
    app, "HrmsApiStack",
    user_pool=identity.user_pool,
    create_employee_fn=compute.create_employee_fn,
    get_upload_url_fn=compute.get_upload_url_fn,
    process_upload_fn=compute.process_upload_fn,
    env=env
)

app.synth()