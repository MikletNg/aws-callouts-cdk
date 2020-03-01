/* eslint-disable */
// this is an auto generated file. This will be overwritten

export const getLatestCallReportRecords = /* GraphQL */ `
  query GetLatestCallReportRecords($limit: Int!) {
    getLatestCallReportRecords(limit: $limit) {
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
export const getLatestCallTaskRecords = /* GraphQL */ `
  query GetLatestCallTaskRecords($limit: Int!) {
    getLatestCallTaskRecords(limit: $limit) {
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
