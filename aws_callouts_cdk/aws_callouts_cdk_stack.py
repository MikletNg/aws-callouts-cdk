from aws_cdk import (
    core,
    aws_lambda as _lambda,
    aws_s3 as _s3,
    aws_s3_deployment as _s3d,
    aws_iam as _iam,
    aws_sqs as _sqs,
    aws_sns as _sns,
    aws_dynamodb as _dynamodb,
    aws_lambda_event_sources as _les,
    aws_stepfunctions as _sfn,
    aws_appsync as _appsync,
    aws_cognito as _cognito,
    aws_cloudfront as _clf
)
import json
import pathlib


class AwsCalloutsCdkStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, instance_id: str, contact_flow_id: str, source_phone_number: str,
                 timeout: int, **kwargs):
        super().__init__(scope, id, **kwargs)

        web_bucket = _s3.Bucket(self, "StaticWebBucket",
                                website_index_document="index.html",
                                website_error_document="index.html",
                                removal_policy=core.RemovalPolicy.DESTROY)

        # web_distribution = _clf.CloudFrontWebDistribution(self, 'StaticWebDistribution',
        #                                                   origin_configs=[_clf.SourceConfiguration(
        #                                                       s3_origin_source=_clf.S3OriginConfig(
        #                                                           s3_bucket_source=web_bucket),
        #                                                       behaviors=[_clf.Behavior(is_default_behavior=True)])],
        #                                                   viewer_protocol_policy=_clf.ViewerProtocolPolicy.REDIRECT_TO_HTTPS)
        #
        # _s3d.BucketDeployment(self, "S3StaticWebContentDeploymentWithInvalidation",
        #                       sources=[
        #                           _s3d.Source.asset(f"{pathlib.Path(__file__).parent.absolute()}/site-content/build")],
        #                       destination_bucket=web_bucket,
        #                       distribution=web_distribution,
        #                       distribution_paths=["/*"],
        #                       storage_class=_s3.StorageClass.INTELLIGENT_TIERING)

        file_bucket = _s3.Bucket(self, "FileBucket",
                                 removal_policy=core.RemovalPolicy.DESTROY)

        call_dead_letter_queue = _sqs.Queue(self, "CallDeadLetterQueue", fifo=True, content_based_deduplication=True)

        call_sqs_queue = _sqs.Queue(self, "CallSqsQueue",
                                    fifo=True,
                                    content_based_deduplication=True,
                                    visibility_timeout=core.Duration.seconds(120),
                                    dead_letter_queue=_sqs.DeadLetterQueue(max_receive_count=1,
                                                                           queue=call_dead_letter_queue))

        async_call_dead_letter_queue = _sqs.Queue(self, "AsyncCallDeadLetterQueue", fifo=True,
                                                  content_based_deduplication=True)

        async_callout_queue = _sqs.Queue(self, "AsyncCalloutQueue",
                                         fifo=True,
                                         content_based_deduplication=True,
                                         visibility_timeout=core.Duration.seconds(120),
                                         dead_letter_queue=_sqs.DeadLetterQueue(max_receive_count=1,
                                                                                queue=async_call_dead_letter_queue))

        call_job_complete_sns_topic = _sns.Topic(self, "CallJobCompleteSnsTopic", display_name="CallJobCompletion")

        call_result_table = _dynamodb.Table(self, "CallResultDynamodbTable",
                                            billing_mode=_dynamodb.BillingMode.PAY_PER_REQUEST,
                                            partition_key=_dynamodb.Attribute(name="task_id",
                                                                              type=_dynamodb.AttributeType.STRING),
                                            sort_key=_dynamodb.Attribute(name="receiver_id",
                                                                         type=_dynamodb.AttributeType.STRING),
                                            removal_policy=core.RemovalPolicy.DESTROY
                                            )

        callout_record_table = _dynamodb.Table(self, "CallTaskDynamodbTable",
                                               billing_mode=_dynamodb.BillingMode.PAY_PER_REQUEST,
                                               partition_key=_dynamodb.Attribute(name="task_id",
                                                                                 type=_dynamodb.AttributeType.STRING),
                                               sort_key=_dynamodb.Attribute(name="created_at",
                                                                            type=_dynamodb.AttributeType.NUMBER),
                                               removal_policy=core.RemovalPolicy.DESTROY
                                               )
        callout_record_table.add_global_secondary_index(
            partition_key=_dynamodb.Attribute(name='call_type', type=_dynamodb.AttributeType.STRING),
            sort_key=_dynamodb.Attribute(name='created_at', type=_dynamodb.AttributeType.NUMBER),
            index_name='CallTypeCreatedAtGlobalIndex',
            projection_type=_dynamodb.ProjectionType.ALL)

        python_function_layer = _lambda.LayerVersion(self, "LambdaPythonFunctionLayer",
                                                     code=_lambda.Code.asset("aws_callouts_cdk/layer/_python"),
                                                     compatible_runtimes=[_lambda.Runtime.PYTHON_3_7,
                                                                          _lambda.Runtime.PYTHON_3_8],
                                                     license="Available under the MIT-0 license")

        nodejs_function_layer = _lambda.LayerVersion(self, "LambdaNodeJsFunctionLayer",
                                                     code=_lambda.Code.asset("aws_callouts_cdk/layer/_nodejs"),
                                                     compatible_runtimes=[_lambda.Runtime.NODEJS_10_X,
                                                                          _lambda.Runtime.NODEJS_12_X],
                                                     license="Available under the MIT-0 license")

        global_python_function_arguments = {
            "code": _lambda.Code.asset("aws_callouts_cdk/src/python"),
            "layers": [python_function_layer],
            "runtime": _lambda.Runtime.PYTHON_3_7
        }

        global_nodeje_function_arguments = {
            "code": _lambda.Code.asset("aws_callouts_cdk/src/nodejs"),
            "layers": [nodejs_function_layer],
            "runtime": _lambda.Runtime.NODEJS_12_X
        }

        get_callout_job_function = _lambda.Function(self, "GetCalloutJobFunction",
                                                    handler="get_call_job.lambda_handler",
                                                    **global_python_function_arguments
                                                    )
        get_callout_job_function.add_environment(key="S3Bucket", value=file_bucket.bucket_name)
        file_bucket.grant_read(get_callout_job_function)

        callout_function = _lambda.Function(self, "CalloutFunction",
                                            handler="send_call.lambda_handler",
                                            **global_python_function_arguments)
        callout_function.add_environment(key="ContactFlowArn",
                                         value=f"arn:aws:connect:{self.region}:{self.account}:instance/{instance_id}/contact-flow/{contact_flow_id}")
        callout_function.add_environment(key="SourcePhoneNumber", value=source_phone_number)
        callout_function.add_environment(key="ExcelFileBucket", value=file_bucket.bucket_name)
        callout_function.add_environment(key="AsynCalloutQueueUrl", value=async_callout_queue.queue_url)
        callout_function.add_to_role_policy(
            statement=_iam.PolicyStatement(
                resources=[f"arn:aws:connect:{self.region}:{self.account}:instance/{instance_id}/*"],
                actions=["connect:StartOutboundVoiceContact"]
            )
        )
        callout_function.add_event_source(
            source=_les.SqsEventSource(queue=async_callout_queue, batch_size=1)
        )
        'arn:aws:connect:751225572132:ap-southeast-2:instance/9d0c7cc5-7d2a-42e4-a3dd-70f402e0d040'
        file_bucket.grant_read_write(callout_function)

        response_handler_function = _lambda.Function(self, "ResponseHandlerFunction",
                                                     handler="response_handler.lambda_handler",
                                                     **global_python_function_arguments
                                                     )
        response_handler_function.add_permission(
            id="ResponseHandlerFunctionLambdaInvokePermission",
            principal=_iam.ServicePrincipal(service="connect.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_account=self.account,
            source_arn=f"arn:aws:connect:{self.region}:{self.account}:instance/{instance_id}"
        )

        send_task_success_function = _lambda.Function(self, "SendTaskSuccessFunction",
                                                      handler="send_task_success.lambda_handler",
                                                      **global_python_function_arguments)
        send_task_success_function.add_permission(
            id="SendTaskSuccessFunctionLambdaInvokePermission",
            principal=_iam.ServicePrincipal(service="connect.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_account=self.account,
            source_arn=f"arn:aws:connect:{self.region}:{self.account}:instance/{instance_id}"
        )

        get_call_result_function = _lambda.Function(self, "GetCallResultFunction",
                                                    handler="get_call_result.lambda_handler",
                                                    memory_size=512,
                                                    **global_python_function_arguments)
        get_call_result_function.add_environment(key="CallResultDynamoDBTable", value=call_result_table.table_name)
        get_call_result_function.add_environment(key="S3Bucket", value=file_bucket.bucket_name)
        call_result_table.grant_read_data(grantee=get_call_result_function)
        file_bucket.grant_read_write(get_call_result_function)

        iterator_function = _lambda.Function(self, "IteratorFunction",
                                             handler="iterator.lambda_handler",
                                             **global_python_function_arguments)
        iterator_function.add_permission(
            id="IteratorFunctionLambdaInvokePermission",
            principal=_iam.ServicePrincipal(service="connect.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_account=self.account,
            source_arn=f"arn:aws:connect:{self.region}:{self.account}:instance/{instance_id}"
        )

        create_appsync_call_task_function = _lambda.Function(self, "CreateAppSyncCallTaskFunction",
                                                             handler="create_appsync_call_task.lambda_handler",
                                                             **global_nodeje_function_arguments)
        create_appsync_call_task_function.add_environment(key="CallSqsQueueUrl", value=call_sqs_queue.queue_url)
        create_appsync_call_task_function.add_environment(key="CallRecordTableName",
                                                          value=callout_record_table.table_name)
        call_sqs_queue.grant_send_messages(create_appsync_call_task_function)
        callout_record_table.grant_write_data(create_appsync_call_task_function)

        create_call_report_record_function = _lambda.Function(self, "CreateCallReportRecordFunction",
                                                              handler="create_call_report_record.lambda_handler",
                                                              **global_nodeje_function_arguments)

        create_excel_call_task_function = _lambda.Function(self, "CreateExcelCallTaskFunction",
                                                           handler="create_excel_call_task.lambda_handler",
                                                           **global_python_function_arguments)
        create_excel_call_task_function.add_environment(key="CallSqsQueueUrl", value=call_sqs_queue.queue_url)
        call_sqs_queue.grant_send_messages(create_excel_call_task_function)

        create_excel_call_task_function.add_event_source(
            source=_les.S3EventSource(bucket=file_bucket, events=[_s3.EventType.OBJECT_CREATED],
                                      filters=[_s3.NotificationKeyFilter(prefix="call_task",
                                                                         suffix=".xlsx")]))

        start_callout_flow_function = _lambda.Function(self, "StartCalloutFlowFunction",
                                                       handler="start_call_out_flow.lambda_handler",
                                                       reserved_concurrent_executions=1,
                                                       **global_python_function_arguments
                                                       )
        start_callout_flow_function.add_environment(key="CallSqsQueueUrl", value=call_sqs_queue.queue_url)
        start_callout_flow_function.add_environment(key="ResponseHandlerFunctionArn",
                                                    value=response_handler_function.function_arn)
        start_callout_flow_function.add_environment(key="IteratorFunctionArn", value=iterator_function.function_arn)
        start_callout_flow_function.add_environment(key="SendTaskSuccessFunctionArn",
                                                    value=send_task_success_function.function_arn)
        start_callout_flow_function.add_environment(key="S3Bucket", value=file_bucket.bucket_name)
        start_callout_flow_function.add_event_source(
            source=_les.SqsEventSource(queue=call_sqs_queue, batch_size=1))
        file_bucket.grant_read_write(start_callout_flow_function)

        call_state_machine_definition = {
            "Comment": "Reading messages from an SQS queue and iteratively processing each message.",
            "StartAt": "Start",
            "States": {
                "Start": {
                    "Type": "Pass",
                    "Next": "Process Call Messages"
                },
                "Process Call Messages": {
                    "Type": "Map",
                    "Next": "Get Call Result",
                    "InputPath": "$",
                    "ItemsPath": "$",
                    "OutputPath": "$.[0]",
                    "Iterator": {
                        "StartAt": "Get Call out job",
                        "States": {
                            "Get Call out job": {
                                "Type": "Task",
                                "Resource": get_callout_job_function.function_arn,
                                "Next": "Callout with AWS Connect"
                            },
                            "Callout with AWS Connect": {
                                "Type": "Task",
                                "Resource": "arn:aws:states:::sqs:sendMessage.waitForTaskToken",
                                "TimeoutSeconds": timeout,
                                "Parameters": {
                                    "QueueUrl": async_callout_queue.queue_url,
                                    "MessageGroupId": "1",
                                    "MessageBody": {
                                        "Message.$": "$",
                                        "TaskToken.$": "$$.Task.Token"
                                    }
                                },
                                "Catch": [{
                                    "ErrorEquals": ["States.Timeout"],
                                    "ResultPath": None,
                                    "Next": "Call Timeout"
                                }],
                                "Next": "Save call result"
                            },
                            "Call Timeout": {
                                "Type": "Pass",
                                "ResultPath": None,
                                "Next": "Save call result"
                            },
                            "Save call result": {
                                "Type": "Task",
                                "Resource": "arn:aws:states:::dynamodb:putItem",
                                "Parameters": {
                                    "TableName": call_result_table.table_name,
                                    "Item": {
                                        "receiver_id": {"S.$": "$.receiver_id"},
                                        "task_id": {"S.$": "$.task_id"},
                                        "username": {"S.$": "$.username"},
                                        "phone_number": {"S.$": "$.phone_number"},
                                        "status": {"S.$": "$.status"},
                                        "answers": {"S.$": "$.answers"},
                                        "error": {"S.$": "$.error"},
                                        "call_at": {"S.$": "$.call_at"}
                                    }
                                },
                                "ResultPath": "$.Result",
                                "OutputPath": "$.task_id",
                                "End": True
                            }
                        }
                    }
                },
                "Get Call Result": {
                    "Type": "Task",
                    "Resource": get_call_result_function.function_arn,
                    "Next": "Create Call Report Record"
                },
                "Create Call Report Record": {
                    "Type": "Task",
                    "Resource": create_call_report_record_function.function_arn,
                    "Next": "Send Completion message to SNS"
                },
                "Send Completion message to SNS": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::sns:publish",
                    "Parameters": {
                        "TopicArn": call_job_complete_sns_topic.topic_arn,
                        "Message.$": "$"
                    },
                    "Next": "Finish"
                },
                "Finish": {
                    "Type": "Succeed"
                }
            }
        }
        callout_state_machine_role = _iam.Role(self, "CalloutStatesExecutionRole",
                                               assumed_by=_iam.ServicePrincipal(f"states.{self.region}.amazonaws.com"))
        callout_state_machine_role.add_to_policy(_iam.PolicyStatement(
            actions=["sqs:SendMessage", "dynamodb:PutItem", "lambda:InvokeFunction", "SNS:Publish"],
            resources=[async_callout_queue.queue_arn, call_result_table.table_arn,
                       get_callout_job_function.function_arn, get_call_result_function.function_arn,
                       call_job_complete_sns_topic.topic_arn, create_appsync_call_task_function.function_arn,
                       create_call_report_record_function.function_arn]))
        callout_state_machine = _sfn.CfnStateMachine(self, "CalloutStateMachine",
                                                     role_arn=callout_state_machine_role.role_arn,
                                                     definition_string=json.dumps(call_state_machine_definition))
        send_task_success_function.add_to_role_policy(_iam.PolicyStatement(
            actions=["states:SendTaskSuccess"],
            resources=[callout_state_machine.ref]
        ))

        start_callout_flow_function.add_environment(key="CalloutStateMachineArn", value=callout_state_machine.ref)
        start_callout_flow_function.add_to_role_policy(
            _iam.PolicyStatement(effect=_iam.Effect.ALLOW, resources=[callout_state_machine.ref],
                                 actions=['states:StartExecution']))

        user_pool = _cognito.UserPool(self, "UserPool", sign_in_type=_cognito.SignInType.USERNAME)

        user_pool_client = _cognito.UserPoolClient(self, "UserPoolClient", user_pool=user_pool)

        appsync_api = _appsync.GraphQLApi(self, "AppSyncApi", name="AWSCalloutApi",
                                          user_pool_config=_appsync.UserPoolConfig(user_pool=user_pool,
                                                                                   default_action=_appsync.UserPoolDefaultAction.ALLOW),
                                          log_config=_appsync.LogConfig(field_log_level=_appsync.FieldLogLevel.ALL),
                                          schema_definition_file=f"{pathlib.Path(__file__).parent.absolute()}/schema.graphql")

        callout_record_ddb_ds = appsync_api.add_dynamo_db_data_source(name="CalloutRecordDdb",
                                                                      description="Callout Record DynamoDB Data Source",
                                                                      table=callout_record_table)
        callout_record_ddb_ds.create_resolver(type_name="Query",
                                              field_name="getLatestCallTaskRecord",
                                              request_mapping_template=_appsync.MappingTemplate.from_string(
                                                  '{"version":"2017-02-28","operation":"Query","index":"CallTypeCreatedAtGlobalIndex","query":{"expression":"call_type = :call_type","expressionValues":{":call_type":{"S":"TASK"}}},"scanIndexForward":false,"limit":${ctx.args.limit}}'),
                                              response_mapping_template=_appsync.MappingTemplate.dynamo_db_result_list())
        callout_record_ddb_ds.create_resolver(type_name="Query",
                                              field_name="getLatestCallReportRecord",
                                              request_mapping_template=_appsync.MappingTemplate.from_string(
                                                  '{"version":"2017-02-28","operation":"Query","index":"CallTypeCreatedAtGlobalIndex","query":{"expression":"call_type = :call_type","expressionValues":{":call_type":{"S":"REPORT"}}},"scanIndexForward":false,"limit":${ctx.args.limit}}'),
                                              response_mapping_template=_appsync.MappingTemplate.dynamo_db_result_list())
        callout_record_ddb_ds.create_resolver(type_name="Mutation",
                                              field_name="createCallReport",
                                              request_mapping_template=_appsync.MappingTemplate.from_string(
                                                  '{"version":"2017-02-28","operation":"PutItem","key":{"task_id":{"S":"${ctx.args.task_id}"}},"attributeValues":$util.dynamodb.toMapValuesJson($ctx.args.record)}'),
                                              response_mapping_template=_appsync.MappingTemplate.dynamo_db_result_item())

        call_task_lambda_ds = appsync_api.add_lambda_data_source(name="CallTaskLambda",
                                                                 description="Call Task Lambda Data Source",
                                                                 lambda_function=create_appsync_call_task_function)
        call_task_lambda_ds.create_resolver(type_name="Mutation",
                                            field_name="createCallTask",
                                            request_mapping_template=_appsync.MappingTemplate.lambda_request(
                                                "$utils.toJson($ctx.args)"),
                                            response_mapping_template=_appsync.MappingTemplate.lambda_result())

        create_call_report_record_function.add_environment(value=appsync_api.graph_ql_url, key="AppSyncGraphQlApiUrl")

        create_call_report_record_function.add_to_role_policy(statement=_iam.PolicyStatement(
            effect=_iam.Effect.ALLOW,
            actions=['appsync:GraphQL'],
            resources=[f"{appsync_api.arn}/types/Mutation/fields/createCallReport"]
        ))

        core.CfnOutput(self, id="OutputCallSqsQueue", value=call_sqs_queue.queue_arn)
        core.CfnOutput(self, id="OutputCallJobCompletionSNSTopic", value=call_job_complete_sns_topic.topic_arn)
        core.CfnOutput(self, id="OutputExcelFileS3Bucket", value=file_bucket.bucket_name)
        core.CfnOutput(self, id="OutputStaticWebS3Bucket", value=web_bucket.bucket_name)
        core.CfnOutput(self, id="OutputStaticWebUrl", value=web_bucket.bucket_website_url)

        identity_pool = _cognito.CfnIdentityPool(self, "IdentityPool",
                                                 allow_unauthenticated_identities=True,
                                                 cognito_identity_providers=[
                                                     _cognito.CfnIdentityPool.CognitoIdentityProviderProperty(
                                                         provider_name=user_pool.user_pool_provider_name,
                                                         client_id=user_pool_client.user_pool_client_id)])
        identity_pool_unauthorized_role = _iam.Role(self, 'IdentityPoolUnAuthorizedRole',
                                                    assumed_by=_iam.FederatedPrincipal(
                                                        federated="cognito-identity.amazonaws.com",
                                                        assume_role_action="sts:AssumeRoleWithWebIdentity",
                                                        conditions={
                                                            "StringEquals": {
                                                                "cognito-identity.amazonaws.com:aud": identity_pool.ref
                                                            },
                                                            "ForAnyValue:StringLike": {
                                                                "cognito-identity.amazonaws.com:amr": "unauthenticated"
                                                            }
                                                        }
                                                    ))
        identity_pool_unauthorized_role.add_to_policy(
            _iam.PolicyStatement(effect=_iam.Effect.ALLOW, actions=["appsync:GraphQL"],
                                 resources=[
                                     f"{appsync_api.arn}/types/Query/fields/getLatestCallRecord",
                                     f"{appsync_api.arn}/types/Mutation/fields/createCallRecord",
                                     f"{appsync_api.arn}/types/Subscription/fields/createCallTask",
                                     f"{appsync_api.arn}/types/Subscription/fields/createCallReport"
                                 ]))

        _cognito.CfnIdentityPoolRoleAttachment(self, "CognitoIdentityPoolRoleAttachment",
                                               identity_pool_id=identity_pool.ref,
                                               roles={"unauthenticated": identity_pool_unauthorized_role.role_arn})

        core.CfnOutput(self, id="UserPoolId", value=user_pool.user_pool_id)
        core.CfnOutput(self, id="UserPoolClientId", value=user_pool_client.user_pool_client_id)
        core.CfnOutput(self, id="IdentityPoolId", value=identity_pool.ref)

        # call_task_record_table = _dynamodb.Table(self, 'CallTaskRecordTable',
        #                                          billing_mode=_dynamodb.BillingMode.PAY_PER_REQUEST,
        #                                          partition_key=_dynamodb.Attribute(name='task_id',
        #                                                                            type=_dynamodb.AttributeType.STRING),
        #                                          sort_key=_dynamodb.Attribute(name='create_at',
        #                                                                       type=_dynamodb.AttributeType.NUMBER))
        #
        # call_report_record_table = _dynamodb.Table(self, 'CallReportRecordTable',
        #                                            billing_mode=_dynamodb.BillingMode.PAY_PER_REQUEST,
        #                                            partition_key=_dynamodb.Attribute(name='report_id',
        #                                                                              type=_dynamodb.AttributeType.STRING),
        #                                            sort_key=_dynamodb.Attribute(name='create_at',
        #                                                                         type=_dynamodb.AttributeType.NUMBER))
        #
        # api = _appsync.GraphQLApi(self, 'AppSyncGraphQlApi', name='aws-callout-api',
        #                           log_config=_appsync.LogConfig(field_log_level=_appsync.FieldLogLevel.ALL),
        #                           schema_definition_file='schema.graphql')
        #
        # call_task_ds = api.add_dynamo_db_data_source(name='CallTaskTableDataSource',
        #                                              description='Call Task Table DataSource',
        #                                              table=call_task_table)
        # call_task_ddb_ds
        #
        # call_report_ds = api.add_dynamo_db_data_source(name='CallReportTableDataSource',
        #                                                description='Call Report Table DataSource',
        #                                                table=call_task_table)

        # sm_start = _sfn.Pass(self, "Start")
        # sm_get_callout_job = _sfn.Task(self, "GetCallOutJob",
        #                                task=_sfn_tasks.RunLambdaTask(lambda_function=get_callout_job_function))
        # sm_call_timeout = _sfn.Pass(self, "CallTimeout", result_path=None)
        # sm_callout_with_amazon_connect = _sfn.Task(self, "CalloutWithAmazonConnect",
        #                                            timeout=core.Duration.seconds(300),
        #                                            task=_sfn_tasks.SendToQueue(queue=async_callout_queue,
        #                                                                        message_group_id="1",
        #                                                                        message_body=_sfn.TaskInput().from_object(
        #                                                                            {
        #                                                                                "QueueUrl": async_callout_queue.queue_url,
        #                                                                                "MessageGroupId": "1",
        #                                                                                "MessageBody": {
        #                                                                                    "Message.$": "$",
        #                                                                                    "TaskToken.$": "$$.Task.Token"
        #                                                                                }
        #                                                                            }))
        #                                            )
        # sm_callout_with_amazon_connect.add_catch(sm_call_timeout, result_path=None, errors=["States.Timeout"])
        # sm_save_call_result = _sfn.Task(self, "SaveCallResult",
        #                                 result_path="$.Result",
        #                                 output_path="$.task_id",
        #                                 parameters={
        #                                     "TableName": call_result_table.table_name,
        #                                     "Item": {
        #                                         "receiver_id": {"S.$": "$.receiver_id"},
        #                                         "task_id": {"S.$": "$.task_id"},
        #                                         "username": {"S.$": "$.username"},
        #                                         "phone_number": {"S.$": "$.phone_number"},
        #                                         "status": {"S.$": "$.status"},
        #                                         "answers": {"S.$": "$.answers"},
        #                                         "error": {"S.$": "$.error"},
        #                                         "call_at": {"S.$": "$.call_at"}
        #                                     }
        #                                 })
        # sm_process_call_messages = _sfn.Map(self, "ProcessCallMessages",
        #                                     input_path="$",
        #                                     items_path="$",
        #                                     output_path="$.[0]")
        # sm_process_call_messages.iterator()
        # callout_state_machine = _sfn.StateMachine(self, "CalloutStateMachine")
        # callout_state_machine.add_to_role_policy(statement=_iam.PolicyStatement(
        #     actions=["sqs:SendMessage", "dynamodb:PutItem", "lambda:InvokeFunction", "SNS:Publish"],
        #     resources=[async_callout_queue.queue_arn, call_result_table.table_arn,
        #                get_callout_job_function.function_arn, get_call_result_function.function_arn,
        #                call_job_complete_sns_topic.topic_arn],
        # ))
