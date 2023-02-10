#!/bin/bash

# AWS Version check
aws_version=$(aws --version)
echo "$aws_version"

# AWS CLI v2 command
error_message=$(aws lambda invoke --function-name expense-report-generator \
--invocation-type RequestResponse --payload file://events/test-sqs-event.json \
--cli-binary-format raw-in-base64-out /tmp/lambda-response.txt | grep "FunctionError")
echo "$error_message"

# Exit if error received from Lambda invocation
if [ -z "$error_message" ]
then
  echo "Success returned from Lambda"
  exit 0
else
  echo "Error returned from Lambda"
  exit 1
fi