import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_cognito as cognito,
    CfnOutput,
    RemovalPolicy
)
from constructs import Construct

class IdentityStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. Create Cognito User Pool
        self.user_pool = cognito.UserPool(
            self, "HrmsUserPool",
            user_pool_name="User pool - realm",
            self_sign_up_enabled=False,
            sign_in_aliases=cognito.SignInAliases(username=True, email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True),
                given_name=cognito.StandardAttribute(required=True, mutable=True)
            ),
            custom_attributes={
                "employee_id": cognito.StringAttribute(mutable=True),
                "department": cognito.StringAttribute(mutable=True),
                "role": cognito.StringAttribute(mutable=True),
                "manager": cognito.StringAttribute(mutable=True),
                "joining_date": cognito.StringAttribute(mutable=True),
                "employment_type": cognito.StringAttribute(mutable=True)
            },
            removal_policy=RemovalPolicy.DESTROY 
        )

        # 2. Create User Pool Client
        self.user_pool_client = self.user_pool.add_client(
            "HrmsWebClient",
            user_pool_client_name="hrms-web-client",
            generate_secret=False,
            auth_flows=cognito.AuthFlow(
                user_srp=True,
                admin_user_password=True,
                user_password=True
            )
        )

        # 3. Create User Pool Group (HR)
        cognito.CfnUserPoolGroup(self, "AdminsGroup",
            user_pool_id=self.user_pool.user_pool_id,
            group_name="HR",
            description="HR Administrators with full access"
        )

        CfnOutput(self, "UserPoolId", value=self.user_pool.user_pool_id)
        CfnOutput(self, "UserPoolClientId", value=self.user_pool_client.user_pool_client_id)