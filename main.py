from globals import expense_map, sender_email
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import matplotlib.pyplot as plt
import numpy as np
import re
import boto3
import botocore
import urllib.parse
import json


txn_start = '$ Amount'
txn_end = 'Total fees charged'
misc_category = 'Miscellaneous'


def fetch_contents(bucket_name: str, file: str):
    """
    This function will read the contents of the file from the S3 bucket's PutObject event and
    return it back for further processing
    :param bucket_name: String S3 bucket name
    :param file: String key from S3 event
    :return: List contents
    """
    contents = list()
    try:
        s3_client = boto3.client('s3')
        if file.endswith('.txt'):
            data = s3_client.get_object(Bucket=bucket_name, Key=file)
            s3_contents = data['Body'].read().splitlines()
            # Convert byte to string
            [contents.append(c.decode()) for c in s3_contents]
    except botocore.exceptions.ClientError as error:
        raise error
    return contents


def parse_stmt_date(transactions: list):
    """
    This function parses the transaction lines and finds the statement start-end date for the
    final expense report
    :param transactions: List of string
    :return: string of date range
    """
    for txn in transactions:
        if re.findall("\d{2}\/\d{2}\/\d{2}\s\-\s\d{2}\/\d{2}\/\d{2}", txn):
            stmt_dates = re.findall("\d{2}\/\d{2}\/\d{2}\s\-\s\d{2}\/\d{2}\/\d{2}", txn)
            print(f'Expense Report for Statement: {stmt_dates[0]}')
            return stmt_dates


def categorize_transactions(transactions: list):
    """
    This functions takes the list of transactions, finds the lines which are valid transaction
    lines i.e. those lines that have an amount associated with it as mentioned in the regex
    :param transactions: list of string
    :return: dict of expenses
    """
    expenses = dict()
    expenses_classified = dict()
    for txn in transactions:
        # Filter transactions which have a date and no negatives i.e. payments
        if re.findall("\d+\/\d+", txn) and not re.findall("-\d+\.\d+", txn) \
                and (re.findall("\d+\.\d+", txn) or re.findall("\.\d+", txn)):
            # Parsing the amount from txn using one of the formats as specified
            amount = re.findall("\d+\,\d+\.\d+", txn) or re.findall("\d+\.\d+", txn) \
                     or re.findall("\.\d+", txn)
            txn_found = False
            for expense_category, expense_values in expense_map.items():
                if any(val.lower() in txn.lower() for val in expense_values):
                    if expense_category not in expenses:
                        expenses_classified[expense_category] = list()
                        # Replace commas for number > 999
                        expenses[expense_category] = round(float(amount[0].replace(',', '')), 2)
                    else:
                        # Replace commas for number > 999
                        expenses[expense_category] = round(expenses[expense_category]
                                                           + float(amount[0].replace(',', '')), 2)
                    expenses_classified[expense_category].append(txn)
                    txn_found = True
                    break
            if not txn_found:
                if misc_category not in expenses:
                    expenses_classified[misc_category] = list()
                    # Replace commas for number > 999
                    expenses[misc_category] = round(float(amount[0].replace(',', '')), 2)
                else:
                    expenses[misc_category] = round(expenses[misc_category] +
                                                    float(amount[0].replace(',', '')), 2)
                expenses_classified[misc_category].append(txn)
    print('\n')
    print('*'*50)
    print('DETAILED EXPENSES')
    print('*'*50)
    for category, txn in expenses_classified.items():
        print(category)
        [print(t) for t in txn]
    print('\n')
    print('*' * 50)
    print('TOTAL EXPENSES')
    print('*' * 50)
    print(expenses)
    return expenses


def plot_expenses(expenses_tot: dict, s_dates: list):
    """
    This function will generate a pie chart with the provided Total expenses
    :param expenses_tot: Dict of total expenses
    :param s_dates: String of statement date
    """
    stats_tot = np.array(list(expenses_tot.values()))
    stats_cat = np.array(list(expenses_tot.keys()))
    explosion = [0.1] * len(list(expenses_tot.keys()))
    plt.pie(stats_tot, labels=stats_cat, explode=explosion,
            autopct=lambda x: '{:.2f}'.format(x*stats_tot.sum()/100))
    plt.title(f'Expense Report for Statement: {s_dates[0]}\n')
    save_img = 'results/report.png'
    plt.savefig(save_img)


def send_email(expenses_tot: dict, s_dates: list):
    """
    This function will use the Amazon AWS Simple Email Service to send the email with expenses
    and the expense pie chart
    :param expenses_tot: Dict of total expenses
    :param s_dates: String of statement date
    """
    ses_client = boto3.client('ses')
    email_list_response = ses_client.list_identities(IdentityType='EmailAddress',
                                                     NextToken='', MaxItems=100)
    destinations = list()
    for email in email_list_response['Identities']:
        destinations.append(email)
    msg = MIMEMultipart()
    mail_title = f'Expense Report: {s_dates[0]}\n'
    msg["Subject"] = mail_title
    msg["From"] = sender_email
    msg["To"] = ",".join(destinations)
    # Set message body
    expenses_str = '----- Expenses Classified ----- \n'
    for k,v in expenses_tot.items():
        expenses_str += k + ': $' + str(v) + '\n'
    expenses_str += '\n'
    body = MIMEText(expenses_str)
    msg.attach(body)
    # Set the file as attachment
    filename = "results/report.png"
    with open(filename, "rb") as attachment:
        part = MIMEApplication(attachment.read())
        part.add_header("Content-Disposition",
                        "attachment",
                        filename=filename)
    msg.attach(part)
    # Convert message to string and send
    response = ses_client.send_raw_email(
        Source = sender_email,
        Destinations = destinations,
        RawMessage = {"Data": msg.as_string()}
    )


def lambda_handler(event, context):
    event_body = json.loads(event['Records'][0]['body'])
    bucket = event_body['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event_body['Records'][0]['s3']['object']['key'],
                                    encoding='utf-8')
    file_contents = fetch_contents(bucket, key)
    dates = parse_stmt_date(file_contents)
    expenses_all = categorize_transactions(file_contents)
    plot_expenses(expenses_all, dates)
    send_email(expenses_all, dates)


if __name__ == '__main__':
    with open('events/test-sqs-event.json') as f:
        test_event = json.load(f)
        lambda_handler(test_event, None)

