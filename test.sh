#!/bin/bash

# AWS CLI v1 command
error_message=$(aws lambda invoke --function-name expense-report-generator \
--invocation-type RequestResponse --payload file://events/test-sqs-event.json \
/tmp/lambda-response.txt | grep "FunctionError")
  # Exit if error received from Lambda invocation
echo "$error_message"

if [ -z "$error_message" ]
then
  echo "Success returned from Lambda"
  exit 0
else
  echo "Error returned from Lambda"
  exit 1
fi