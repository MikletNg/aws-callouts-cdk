/* eslint-disable */
// this is an auto generated file. This will be overwritten

export const createCallTask = /* GraphQL */ `
  subscription CreateCallTask {
    createCallTask {
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
export const createCallReport = /* GraphQL */ `
  subscription CreateCallReport {
    createCallReport {
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
