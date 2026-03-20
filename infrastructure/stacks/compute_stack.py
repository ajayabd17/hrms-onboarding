from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_iam as iam,
)
from constructs import Construct
from pathlib import Path
import os


class ComputeStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        employee_table,
        workflow_table,
        stage_status_table,
        document_table,
        user_pool,
        user_pool_client_id: str,
        docs_bucket,
        hr_topic,
        frontend_origin: str,
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)
        lambdas_root = Path(__file__).resolve().parents[2] / "lambdas"
        ses_from_email = self.node.try_get_context("sesFromEmail") or os.environ.get("HRMS_SES_FROM_EMAIL", "")

        common_env = {
            "EMPLOYEE_TABLE": employee_table.table_name,
            "WORKFLOW_TABLE": workflow_table.table_name,
            "STAGE_STATUS_TABLE": stage_status_table.table_name,
            "DOCUMENT_TABLE": document_table.table_name,
            "USER_POOL_ID": user_pool.user_pool_id,
            "COGNITO_CLIENT_ID": user_pool_client_id,
            "DOCS_BUCKET_NAME": docs_bucket.bucket_name,
            "HR_TOPIC_ARN": hr_topic.topic_arn,
            "ALLOWED_ORIGIN": frontend_origin,
            "ALLOWED_ORIGINS": ",".join([
                frontend_origin,
                "http://localhost:5173",
                "http://hrms-onboarding.s3-website.ap-south-1.amazonaws.com",
            ]),
            "STATE_MACHINE_NAME": "hrms-onboarding-workflow",
            "PORTAL_URL": frontend_origin,
            "SES_FROM_EMAIL": ses_from_email,
            "EMPLOYEE_GROUP": os.environ.get("HRMS_EMPLOYEE_GROUP", "employee"),
        }

        self.auth_login_fn = _lambda.Function(
            self, "AuthLoginFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="auth_login.handler",
            code=_lambda.Code.from_asset(str(lambdas_root / "auth_login")),
            environment=common_env,
            timeout=Duration.seconds(30),
        )

        self.auth_complete_new_password_fn = _lambda.Function(
            self, "AuthCompleteNewPasswordFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="auth_complete_new_password.handler",
            code=_lambda.Code.from_asset(str(lambdas_root / "auth_complete_new_password")),
            environment=common_env,
            timeout=Duration.seconds(30),
        )

        self.create_employee_fn = _lambda.Function(
            self, "CreateEmployeeFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="create_employee.handler",
            code=_lambda.Code.from_asset(str(lambdas_root / "create_employee")),
            environment=common_env,
            timeout=Duration.seconds(30),
        )

        self.get_upload_url_fn = _lambda.Function(
            self, "GetUploadUrlFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="get_upload_url.handler",
            code=_lambda.Code.from_asset(str(lambdas_root / "get_upload_url")),
            environment=common_env,
            timeout=Duration.seconds(30),
        )

        self.process_upload_fn = _lambda.Function(
            self, "ProcessUploadFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="process_upload.handler",
            code=_lambda.Code.from_asset(str(lambdas_root / "process_upload")),
            environment=common_env,
            timeout=Duration.seconds(30),
        )

        self.stage_executor_fn = _lambda.Function(
            self, "StageExecutorFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="stage_executor.handler",
            code=_lambda.Code.from_asset(str(lambdas_root / "stage_executor")),
            environment=common_env,
            timeout=Duration.seconds(30),
        )

        self.progress_api_fn = _lambda.Function(
            self, "ProgressApiFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="progress_api.handler",
            code=_lambda.Code.from_asset(str(lambdas_root / "progress_api")),
            environment=common_env,
            timeout=Duration.seconds(30),
        )

        self.list_employees_fn = _lambda.Function(
            self, "ListEmployeesFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="list_employees.handler",
            code=_lambda.Code.from_asset(str(lambdas_root / "list_employees")),
            environment=common_env,
            timeout=Duration.seconds(30),
        )

        self.reminder_trigger_fn = _lambda.Function(
            self, "ReminderTriggerFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="reminder_trigger.handler",
            code=_lambda.Code.from_asset(str(lambdas_root / "reminder_trigger")),
            environment=common_env,
            timeout=Duration.seconds(30),
        )

        self.complete_stage_fn = _lambda.Function(
            self, "CompleteStageFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="complete_stage.handler",
            code=_lambda.Code.from_asset(str(lambdas_root / "complete_stage")),
            environment=common_env,
            timeout=Duration.seconds(30),
        )

        self.finalize_onboarding_fn = _lambda.Function(
            self, "FinalizeOnboardingFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="finalize_onboarding.handler",
            code=_lambda.Code.from_asset(str(lambdas_root / "finalize_onboarding")),
            environment=common_env,
            timeout=Duration.seconds(30),
        )

        for fn in [
            self.create_employee_fn,
            self.process_upload_fn,
            self.stage_executor_fn,
            self.progress_api_fn,
            self.list_employees_fn,
            self.reminder_trigger_fn,
            self.complete_stage_fn,
            self.finalize_onboarding_fn,
        ]:
            employee_table.grant_read_write_data(fn)
            workflow_table.grant_read_write_data(fn)
            stage_status_table.grant_read_write_data(fn)
            document_table.grant_read_write_data(fn)

        docs_bucket.grant_put(self.get_upload_url_fn)
        docs_bucket.grant_read(self.process_upload_fn)
        hr_topic.grant_publish(self.process_upload_fn)

        self.create_employee_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cognito-idp:AdminCreateUser", "cognito-idp:AdminAddUserToGroup"],
                resources=[user_pool.user_pool_arn],
            )
        )

        for fn in [self.auth_login_fn, self.auth_complete_new_password_fn]:
            fn.add_to_role_policy(
                iam.PolicyStatement(
                    actions=["cognito-idp:InitiateAuth", "cognito-idp:RespondToAuthChallenge"],
                    resources=[user_pool.user_pool_arn],
                )
            )

        for fn in [self.create_employee_fn, self.process_upload_fn, self.complete_stage_fn]:
            fn.add_to_role_policy(
                iam.PolicyStatement(
                    actions=["states:StartExecution", "states:SendTaskSuccess"],
                    resources=["*"],
                )
            )

        for fn in [self.stage_executor_fn, self.reminder_trigger_fn]:
            fn.add_to_role_policy(
                iam.PolicyStatement(
                    actions=["events:PutRule", "events:PutTargets", "events:DeleteRule", "events:RemoveTargets"],
                    resources=["*"],
                )
            )

        for fn in [self.create_employee_fn, self.reminder_trigger_fn]:
            fn.add_to_role_policy(
                iam.PolicyStatement(actions=["ses:SendEmail", "ses:SendRawEmail"], resources=["*"])
            )

    def bind_reminder_lambda(self):
        self.stage_executor_fn.add_environment("REMINDER_LAMBDA_ARN", self.reminder_trigger_fn.function_arn)
