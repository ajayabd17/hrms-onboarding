from aws_cdk import Stack, CfnOutput, aws_sns as sns
from constructs import Construct


class MessagingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        self.hr_topic = sns.Topic(self, 'HrAlertsTopic', display_name='HR Onboarding Alerts')

        CfnOutput(self, 'HrTopicArn', value=self.hr_topic.topic_arn)
