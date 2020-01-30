#!/usr/bin/env python3

from aws_cdk import core

from aws_callouts_cdk.aws_callouts_cdk_stack import AwsCalloutsCdkStack

env_dev = core.Environment(account="751225572132", region="ap-northeast-1")

app = core.App()
AwsCalloutsCdkStack(app, "aws-callouts-cdk", env=env_dev, instance_id="2", contact_flow_id='', source_phone_number='',
                    timeout=300)

app.synth()
