/* eslint-disable */
// this is an auto generated file. This will be overwritten

export const getLatestCallTaskRecord = /* GraphQL */ `
  query GetLatestCallTaskRecord($limit: Int!) {
    getLatestCallTaskRecord(limit: $limit) {
      call_type
      task_id
      created_at
      greeting
      ending
      questions {
        question_template
        question_type
      }
      receivers {
        phone_number
        username
        id
        receiver_id
      }
    }
  }
`;
export const getLatestCallReportRecord = /* GraphQL */ `
  query GetLatestCallReportRecord($limit: Int!) {
    getLatestCallReportRecord(limit: $limit) {
      call_type
      task_id
      created_at
      report_path {
        bucket_name
        key
        prefix
      }
      presigned_url
    }
  }
`;
export const getLatestCallRecords = /* GraphQL */ `
  query GetLatestCallRecords($call_type: CallRecordType!, $limit: Int!) {
    getLatestCallRecords(call_type: $call_type, limit: $limit) {
      ... on CallTask {
        call_type
        task_id
        created_at
        greeting
        ending
        questions {
          question_template
          question_type
        }
        receivers {
          phone_number
          username
          id
          receiver_id
        }
      }
      ... on CallReport {
        call_type
        task_id
        created_at
        report_path {
          bucket_name
          key
          prefix
        }
        presigned_url
      }
    }
  }
`;
