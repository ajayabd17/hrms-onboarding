from aws_cdk import (
    Stack,
    aws_apigateway as apigw,
    CfnOutput
)
from constructs import Construct

class ApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str,
                 user_pool, create_employee_fn, get_upload_url_fn, process_upload_fn,
                 **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # 1. Create API Gateway
        self.api = apigw.RestApi(
            self, "HrmsApi",
            rest_api_name="HRMS API",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS
            )
        )

        # 2. Create Cognito User Pool Authorizer
        self.authorizer = apigw.CognitoUserPoolsAuthorizer(
            self, "HrmsAuthorizer",
            cognito_user_pools=[user_pool]
        )

        # 3. Routes & Integrations
        
        # POST /employees
        employees = self.api.root.add_resource("employees")
        employees.add_method(
            "POST",
            apigw.LambdaIntegration(create_employee_fn),
            authorizer=self.authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO
        )

        # /uploads
        uploads = self.api.root.add_resource("uploads")
        
        # GET /uploads/url
        upload_url = uploads.add_resource("url")
        upload_url.add_method(
            "GET",
            apigw.LambdaIntegration(get_upload_url_fn),
            authorizer=self.authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO
        )

        # POST /uploads/process
        upload_process = uploads.add_resource("process")
        upload_process.add_method(
            "POST",
            apigw.LambdaIntegration(process_upload_fn),
            authorizer=self.authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO
        )

        CfnOutput(self, "ApiEndpoint", value=self.api.url)
