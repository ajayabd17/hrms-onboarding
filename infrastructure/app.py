#!/usr/bin/env python3
import aws_cdk as cdk
import os

from stacks.storage_stack import StorageStack
from stacks.identity_stack import IdentityStack
from stacks.compute_stack import ComputeStack

app = cdk.App()

env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "ap-south-1")
)

# 1. Storage
storage = StorageStack(app, "HrmsStorageStack", env=env)

# 2. Identity
identity = IdentityStack(app, "HrmsIdentityStack", env=env)

# 3. Compute (ONLY gets names, not resources)
compute = ComputeStack(
    app, "HrmsComputeStack",
    employee_table=storage.employee_table,
    user_pool=identity.user_pool,
    docs_bucket_name=storage.docs_bucket.bucket_name,
    env=env
)

app.synth()