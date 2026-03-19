import aws_cdk.aws_s3_notifications as s3n
import aws_cdk.aws_lambda as _lambda
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

        # GSI for email lookup
        self.employee_table.add_global_secondary_index(
            index_name="email-index",
            partition_key=dynamodb.Attribute(
                name="email",
                type=dynamodb.AttributeType.STRING
            )
        )

        # 2. Stage Status Table
        self.stage_table = dynamodb.Table(
            self, "StageStatusTable",
            partition_key=dynamodb.Attribute(
                name="employee_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="stage_name",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        # 3. Documents Bucket
        self.docs_bucket = s3.Bucket(
            self, "HrmsDocumentsBucket",
            encryption=s3.BucketEncryption.S3_MANAGED,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            cors=[s3.CorsRule(
                allowed_methods=[
                    s3.HttpMethods.PUT,
                    s3.HttpMethods.GET
                ],
                allowed_origins=["http://localhost:5173"],  # safer than *
                allowed_headers=["*"],
                exposed_headers=["ETag"]
            )]
        )

        # Outputs
        CfnOutput(self, "EmployeeTableName",
                  value=self.employee_table.table_name)

        CfnOutput(self, "DocsBucketName",
                  value=self.docs_bucket.bucket_name)

    # 🔥 IMPORTANT: Add S3 trigger HERE (not in compute stack)
    def add_s3_trigger(self, lambda_arn: str):
        fn = _lambda.Function.from_function_arn(
        self,
        "ImportedProcessUploadFn",
        lambda_arn
        )

        self.docs_bucket.add_event_notification(
        s3.EventType.OBJECT_CREATED,
        s3n.LambdaDestination(fn),
        s3.NotificationKeyFilter(prefix="documents/")
        )