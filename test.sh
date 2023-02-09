#!/bin/bash

error_message=$(aws lambda invoke --function-name expense-report-generator \
--invocation-type RequestResponse --payload file://events/test-sqs-event.json \
--cli-binary-format raw-in-base64-out /dev/stdout | grep "errorMessage")
  # Exit if error received from Lambda invocation
echo $error_message
if [ ! -z "$error_message" ]
then
  echo "Error returned from Lambda"
  exit 1
else
  echo "Success returned from Lambda"
fi