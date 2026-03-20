import os
from aws_cdk import Stack, CfnOutput, aws_sns as sns, aws_sns_subscriptions as subs
from constructs import Construct


class MessagingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        self.hr_topic = sns.Topic(self, 'HrAlertsTopic', display_name='HR Onboarding Alerts')
        hr_email = self.node.try_get_context("hrAlertEmail") or os.environ.get("HRMS_HR_ALERT_EMAIL", "")
        if hr_email:
            self.hr_topic.add_subscription(subs.EmailSubscription(hr_email))

        CfnOutput(self, 'HrTopicArn', value=self.hr_topic.topic_arn)
