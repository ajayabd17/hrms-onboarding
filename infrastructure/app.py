#!/usr/bin/env python3
import aws_cdk as cdk
import os
from stacks.storage_stack import StorageStack
from stacks.identity_stack import IdentityStack

app = cdk.App()

# Default environment for deployment
env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "ap-south-1")
)

# Initialize the Storage Stack
StorageStack(app, "HrmsStorageStack", env=env)

# Initialize the Identity Stack
IdentityStack(app, "HrmsIdentityStack", env=env)

app.synth()