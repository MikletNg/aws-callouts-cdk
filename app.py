#!/usr/bin/env python3

from aws_cdk import core

from aws_callouts_cdk.aws_callouts_cdk_stack import AwsCalloutsCdkStack


app = core.App()
AwsCalloutsCdkStack(app, "aws-callouts-cdk")

app.synth()
