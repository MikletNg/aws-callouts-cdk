const AppSync = require('aws-appsync').default;
const AWS = require('aws-sdk');
const moment = require('moment-timezone');
const _ = require('lodash');
const gql = require('graphql-tag');
require('cross-fetch/polyfill');

const mutation = gql(`
    mutation createCallReport($report: ICallReport!){
        createCallReport(report: $report){
            call_type
            task_id
            created_at
            report_path{
                bucket_name
                key
                prefix
            }
            presigned_url
        }
    }
`);

exports.lambda_handler = async (evt, ctx) => {
    console.log(JSON.stringify(evt, null, 2));

    const msg = {
        call_type: 'REPORT',
        task_id: evt.TaskId,
        report_path: {
            bucket_name: evt.Bucket,
            key: evt.ExcelKey,
        },
        presigned_url: evt.ExcelDownloadUrl,
        created_at: moment().unix()
    };
    console.log({ msg });

    const AppSyncClient = new AppSync({
        url: process.env.AppSyncGraphQlApiUrl,
        region: process.env.AWS_REGION,
        auth: {
            type: 'AWS_IAM',
            credentials: AWS.config.credentials
        },
        disableOffline: true
    });

    const mutate_res = await AppSyncClient.mutate({ mutation, variables: { report: msg } });
    console.log({mutate_res});

    return evt

};