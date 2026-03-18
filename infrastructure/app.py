#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.storage_stack import StorageStack

app = cdk.App()

# Initialize the Storage Stack
StorageStack(app, "HrmsStorageStack")

app.synth()