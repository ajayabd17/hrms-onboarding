from aws_cdk import (
    Stack,
    CfnOutput,
    RemovalPolicy,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
)
from constructs import Construct


class StorageStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # 1. Employee Table
        self.employee_table = dynamodb.Table(
            self, "EmployeeTable",
            partition_key=dynamodb.Attribute(
                name="employee_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        # GSI
        self.employee_table.add_global_secondary_index(
            index_name="email-index",
            partition_key=dynamodb.Attribute(
                name="email",
                type=dynamodb.AttributeType.STRING
            )
        )

        # 2. S3 Bucket
        self.docs_bucket = s3.Bucket(
            self, "HrmsDocumentsBucket",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            cors=[s3.CorsRule(
                allowed_methods=[s3.HttpMethods.PUT, s3.HttpMethods.GET],
                allowed_origins=["http://localhost:5173"],
                allowed_headers=["*"]
            )]
        )

        # Outputs
        CfnOutput(self, "EmployeeTableName",
                  value=self.employee_table.table_name)

        CfnOutput(self, "BucketName",
                  value=self.docs_bucket.bucket_name)