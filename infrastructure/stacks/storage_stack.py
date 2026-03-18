from aws_cdk import (
    Stack,
    CfnOutput,
    RemovalPolicy,
    aws_dynamodb as dynamodb,
    aws_s3 as s3
)
from constructs import Construct

class StorageStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Employee Table - The "Source of Truth"
        self.employee_table = dynamodb.Table(
            self, "EmployeeTable",
            partition_key=dynamodb.Attribute(name="employee_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY  # Use RETAIN for production!
        )

        # Add Global Secondary Index to find employees by email
        self.employee_table.add_global_secondary_index(
            index_name="email-index",
            partition_key=dynamodb.Attribute(name="email", type=dynamodb.AttributeType.STRING)
        )

        # 2. Stage Status Table - Tracks progress (Docs -> IT -> Manager)
        self.stage_table = dynamodb.Table(
            self, "StageStatusTable",
            partition_key=dynamodb.Attribute(name="employee_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="stage_name", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        # 3. Documents Bucket - Where IDs and Offer Letters live
        self.docs_bucket = s3.Bucket(
            self, "HrmsDocumentsBucket",
            encryption=s3.BucketEncryption.S3_MANAGED,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Output the names so other stacks can use them
        CfnOutput(self, "EmployeeTableName", value=self.employee_table.table_name)
        CfnOutput(self, "DocsBucketName", value=self.docs_bucket.bucket_name)