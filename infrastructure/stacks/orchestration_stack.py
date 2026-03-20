from aws_cdk import Stack, CfnOutput
from aws_cdk import (
    aws_stepfunctions as sfn,
    aws_logs as logs,
)
from constructs import Construct
from pathlib import Path


class OrchestrationStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, stage_executor_fn, finalize_onboarding_fn, hr_topic, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        log_group = logs.LogGroup(self, 'OnboardingStateMachineLogs')

        self.state_machine = sfn.StateMachine(
            self,
            'OnboardingStateMachine',
            state_machine_name="hrms-onboarding-workflow",
            definition_body=sfn.DefinitionBody.from_file(
                str(Path(__file__).resolve().parents[2] / "statemachine" / "onboarding.asl.json")
            ),
            definition_substitutions={
                'StageExecutorArn': stage_executor_fn.function_arn,
                'FinalizeLambdaArn': finalize_onboarding_fn.function_arn,
                'HrTopicArn': hr_topic.topic_arn,
            },
            tracing_enabled=True,
            logs=sfn.LogOptions(
                destination=log_group,
                level=sfn.LogLevel.ALL,
                include_execution_data=True,
            ),
            state_machine_type=sfn.StateMachineType.STANDARD,
        )

        CfnOutput(self, "StateMachineArn", value=self.state_machine.state_machine_arn)
