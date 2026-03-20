from aws_cdk import (
    Stack,
    CfnOutput,
    RemovalPolicy,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
)
from constructs import Construct


class StorageStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, frontend_origin: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # 1. Employee Table
        self.employee_table = dynamodb.Table(
            self, "EmployeeTable",
            partition_key=dynamodb.Attribute(
                name="employee_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
            removal_policy=RemovalPolicy.RETAIN
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
            enforce_ssl=True,
            event_bridge_enabled=True,
            removal_policy=RemovalPolicy.RETAIN,
            cors=[s3.CorsRule(
                allowed_methods=[s3.HttpMethods.PUT, s3.HttpMethods.GET],
                allowed_origins=[frontend_origin, "http://localhost:5173"],
                allowed_headers=["*"]
            )]
        )

        self.stage_status_table = dynamodb.Table(
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
            removal_policy=RemovalPolicy.RETAIN
        )

        self.document_table = dynamodb.Table(
            self, "DocumentTable",
            partition_key=dynamodb.Attribute(
                name="employee_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="doc_type",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN
        )

        self.workflow_table = dynamodb.Table(
            self, "WorkflowTable",
            partition_key=dynamodb.Attribute(
                name="employee_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN
        )

        # Outputs
        CfnOutput(self, "EmployeeTableName",
                  value=self.employee_table.table_name)

        CfnOutput(self, "BucketName",
                  value=self.docs_bucket.bucket_name)
        CfnOutput(self, "StageStatusTableName",
                  value=self.stage_status_table.table_name)
        CfnOutput(self, "DocumentTableName",
                  value=self.document_table.table_name)
        CfnOutput(self, "WorkflowTableName",
                  value=self.workflow_table.table_name)
