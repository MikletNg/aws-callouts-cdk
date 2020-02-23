#!/usr/bin/env python3

from aws_cdk import core

from aws_callouts_cdk.aws_callouts_cdk_stack import AwsCalloutsCdkStack

env = core.Environment(account="751225572132", region="ap-southeast-2")

app = core.App()
AwsCalloutsCdkStack(app, "aws-callouts-cdk", env=env,
                    instance_id="9d0c7cc5-7d2a-42e4-a3dd-70f402e0d040",
                    contact_flow_id="d0ec25e8-3d1c-4044-b672-67c89edbe4db",
                    source_phone_number="+85230189276",
                    timeout=300)

app.synth()
