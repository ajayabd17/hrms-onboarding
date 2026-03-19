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

# -------------------------------
# 1. Independent Stacks
# -------------------------------
storage = StorageStack(app, "HrmsStorageStack", env=env)

identity = IdentityStack(app, "HrmsIdentityStack", env=env)

# -------------------------------
# 2. Compute Stack (depends on above)
# -------------------------------
compute = ComputeStack(
    app, "HrmsComputeStack",
    employee_table=storage.employee_table,
    user_pool=identity.user_pool,
    docs_bucket=storage.docs_bucket,
    env=env
)

# -------------------------------
# 🔥 3. CONNECT S3 → LAMBDA HERE
# -------------------------------
storage.add_s3_trigger(compute.process_upload_fn.function_arn)

# -------------------------------
# 4. Synthesize
# -------------------------------
app.synth()