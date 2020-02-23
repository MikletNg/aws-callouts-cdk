const AWS = require('aws-sdk');
const sqs = new AWS.SQS();
const ddb = new AWS.DynamoDB.DocumentClient();
const moment = require('moment-timezone');
const _ = require('lodash');

const q_type = {
    NUMBER: 'Number',
    YES_NO: 'Yes/No',
    DATE: 'Date',
    TIME: 'Time',
    MULTIPLE_CHOICE: 'Multiple Choice',
    OK: 'OK',
};

exports.lambda_handler = async (evt, ctx) => {
    console.log(JSON.stringify(evt, null, 2));
    const {task: TASK} = evt;

    const sqs_msg = JSON.parse(JSON.stringify(TASK));
    sqs_msg.questions.forEach((q, i) => sqs_msg.questions[i].question_type = q_type[q.question_type]);
    console.log(JSON.stringify(sqs_msg));

    await sqs.sendMessage({
        MessageBody: JSON.stringify(sqs_msg),
        MessageGroupId: '1',
        QueueUrl: process.env.CallSqsQueueUrl
    }).promise().then(console.log);

    const ddb_ctx = JSON.parse(JSON.stringify(TASK));
    ddb_ctx.created_at = moment().unix();
    console.log(JSON.stringify(ddb_ctx));

    const response = await ddb.put({TableName: process.env.CallRecordTableName, Item: ddb_ctx}).promise();
    
    console.log(response);

    return ddb_ctx;

};