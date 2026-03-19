from aws_cdk import (
    Stack,
    aws_cognito as cognito,
    CfnOutput
)
from constructs import Construct

class IdentityStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Cognito User Pool
        self.user_pool = cognito.UserPool(
            self, "HrmsUserPool",
            user_pool_name="hrms-user-pool",
            self_sign_up_enabled=False,  # No Self-Signup
            sign_in_aliases=cognito.SignInAliases(username=True, email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            custom_attributes={
                "employee_id": cognito.StringAttribute(mutable=True)  # Data Linking bridge
            }
        )

        # Create User Pool Client
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

        # Outputs
        CfnOutput(self, "UserPoolId", value=self.user_pool.user_pool_id)
        CfnOutput(self, "UserPoolClientId", value=self.user_pool_client.user_pool_client_id)
