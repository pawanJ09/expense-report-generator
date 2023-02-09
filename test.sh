#!/bin/bash

error_message=$(aws lambda invoke --function-name expense-report-generator \
--invocation-type RequestResponse --payload file://events/test-sqs-event.json \
--cli-binary-format raw-in-base64-out /tmp/lambda-response.txt | grep "errorMessage")
  # Exit if error received from Lambda invocation
echo "$error_message"

if [ -n "$error_message" ]
then
  echo "Success returned from Lambda"
  exit 0
else
  echo "Error returned from Lambda"
  exit 1
fi