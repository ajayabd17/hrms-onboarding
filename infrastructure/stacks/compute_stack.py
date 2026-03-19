from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_iam as iam,
    Duration,
)
from constructs import Construct


class ComputeStack(Stack):
    def __init__(self, scope: Construct, construct_id: str,
                 employee_table, user_pool, docs_bucket_name, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # 1. Create Employee Lambda
        self.create_employee_fn = _lambda.Function(
            self, "CreateEmployeeFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="create_employee.handler",
            code=_lambda.Code.from_asset("../lambdas/create_employee"),
            environment={
                "EMPLOYEE_TABLE": employee_table.table_name,
                "USER_POOL_ID": user_pool.user_pool_id
            },
            timeout=Duration.seconds(30)
        )

        # 2. Get Upload URL Lambda
        self.get_upload_url_fn = _lambda.Function(
            self, "GetUploadUrlFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="get_upload_url.handler",
            code=_lambda.Code.from_asset("../lambdas/get_upload_url"),
            environment={
                "DOCS_BUCKET_NAME": docs_bucket_name
            },
            timeout=Duration.seconds(30)
        )

        # 3. Process Upload Lambda
        self.process_upload_fn = _lambda.Function(
            self, "ProcessUploadFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="process_upload.handler",
            code=_lambda.Code.from_asset("../lambdas/process_upload"),
            environment={
                "EMPLOYEE_TABLE": employee_table.table_name
            },
            timeout=Duration.seconds(30)
        )

        # Permissions (ONLY DynamoDB + Cognito)
        employee_table.grant_write_data(self.create_employee_fn)
        employee_table.grant_write_data(self.process_upload_fn)

        self.create_employee_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "cognito-idp:AdminCreateUser",
                    "cognito-idp:AdminAddUserToGroup"
                ],
                resources=[user_pool.user_pool_arn]
            )
        )