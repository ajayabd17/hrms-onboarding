from aws_cdk import Stack, CfnOutput
from aws_cdk import aws_apigateway as apigw
from constructs import Construct


class ApiStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        user_pool,
        auth_login_fn,
        auth_complete_new_password_fn,
        create_employee_fn,
        get_upload_url_fn,
        progress_api_fn,
        complete_stage_fn,
        list_employees_fn,
        frontend_origin: str,
        **kwargs
    ):
        super().__init__(scope, construct_id, **kwargs)

        api = apigw.RestApi(
            self,
            'HrmsApi',
            rest_api_name='hrms-onboarding-api',
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=[
                    frontend_origin,
                    "http://localhost:5173",
                    "http://hrms-onboarding.s3-website.ap-south-1.amazonaws.com",
                ],
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=["Content-Type", "Authorization"],
            )
        )
        api.add_gateway_response(
            "Default4xxWithCors",
            type=apigw.ResponseType.DEFAULT_4_XX,
            response_headers={
                "Access-Control-Allow-Origin": "'*'",
                "Access-Control-Allow-Headers": "'Content-Type,Authorization'",
                "Access-Control-Allow-Methods": "'GET,POST,OPTIONS'",
            },
        )
        api.add_gateway_response(
            "Default5xxWithCors",
            type=apigw.ResponseType.DEFAULT_5_XX,
            response_headers={
                "Access-Control-Allow-Origin": "'*'",
                "Access-Control-Allow-Headers": "'Content-Type,Authorization'",
                "Access-Control-Allow-Methods": "'GET,POST,OPTIONS'",
            },
        )

        authorizer = apigw.CognitoUserPoolsAuthorizer(self, 'HrmsAuthorizer', cognito_user_pools=[user_pool])

        auth = api.root.add_resource('auth')
        auth.add_resource('login').add_method('POST', apigw.LambdaIntegration(auth_login_fn))
        auth.add_resource('complete-new-password').add_method('POST', apigw.LambdaIntegration(auth_complete_new_password_fn))

        employees = api.root.add_resource('employees')
        employees.add_method('POST', apigw.LambdaIntegration(create_employee_fn))
        employees.add_method('GET', apigw.LambdaIntegration(list_employees_fn), authorization_type=apigw.AuthorizationType.COGNITO, authorizer=authorizer)

        upload_url = api.root.add_resource('upload-url')
        upload_url.add_method('GET', apigw.LambdaIntegration(get_upload_url_fn), authorization_type=apigw.AuthorizationType.COGNITO, authorizer=authorizer)

        onboarding = api.root.add_resource('onboarding')
        emp = onboarding.add_resource('{employee_id}')
        emp.add_resource('progress').add_method('GET', apigw.LambdaIntegration(progress_api_fn), authorization_type=apigw.AuthorizationType.COGNITO, authorizer=authorizer)
        emp.add_resource('stage-complete').add_method('POST', apigw.LambdaIntegration(complete_stage_fn), authorization_type=apigw.AuthorizationType.COGNITO, authorizer=authorizer)

        self.api_url = api.url
        CfnOutput(self, "ApiUrl", value=self.api_url)
