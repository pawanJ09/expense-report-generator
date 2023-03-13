from globals import sender_email, tmp_report_path, expense_categories_fetcher_agw, expense_email_verifier_agw
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
import os
import requests


misc_category = 'Miscellaneous'
s3_client = boto3.client("s3")


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


def fetch_expense_map():
    """
    This function fetches the expense categories from expense-categories-fetcher API
    :return: 'Items' from API response
    """
    resp = requests.get(expense_categories_fetcher_agw)
    return resp.json()


def categorize_transactions(transactions: list):
    """
    This functions takes the list of transactions, finds the lines which are valid transaction
    lines i.e. those lines that have an amount associated with it as mentioned in the regex
    :param transactions: list of string
    :return: dict of expenses
    :return: dict of expenses_classified
    """
    expenses = dict()
    expenses_classified = dict()
    fem = fetch_expense_map()
    for txn in transactions:
        # Filter transactions which have a date and no negatives i.e. payments
        if re.findall("\d+\/\d+", txn) and not re.findall("-\d+\.\d+", txn) \
                and (re.findall("\d+\.\d+", txn) or re.findall("\.\d+", txn)):
            # Parsing the amount from txn using one of the formats as specified
            amount = re.findall("\d+\,\d+\.\d+", txn) or re.findall("\d+\.\d+", txn) \
                     or re.findall("\.\d+", txn)
            txn_found = False
            for em in fem:
                expense_category = em['category']
                expense_values = em['val']
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
    return expenses, expenses_classified


def format_expenses(expenses_tot: dict, expenses_cl: dict, is_format: bool):
    """
    This function will print or format the expenses
    :param expenses_tot: Dict of total expenses
    :param expenses_cl: Dict of classified expenses
    :param is_format: boolean to determine if print or return the formatted expenses
    """
    if not is_format:
        print('\n')
        print('*' * 50)
        print('DETAILED EXPENSES')
        print('*' * 50)
        for category, txn in expenses_cl.items():
            print(category)
            [print(t) for t in txn]
        print('\n')
        print('*' * 50)
        print('TOTAL EXPENSES')
        print('*' * 50)
        print(expenses_tot)
    else:
        formatted_expenses = '\n'
        formatted_expenses += '*' * 20
        formatted_expenses += 'DETAILED EXPENSES'
        formatted_expenses += '*' * 20
        for category, txn in expenses_cl.items():
            formatted_expenses += f'\n{category} ==>'
            for t in txn:
                formatted_expenses += f'\n{t}'
        formatted_expenses += '\n\n'
        formatted_expenses += '*' * 20
        formatted_expenses += 'TOTAL EXPENSES'
        formatted_expenses += '*' * 20
        for cat, val in expenses_tot.items():
            formatted_expenses += f'\n{cat}: ${val}'
        formatted_expenses += '\n'
        return formatted_expenses


def plot_expenses(expenses_tot: dict, s_dates: list):
    """
    This function will generate a pie chart with the provided Total expenses
    :param expenses_tot: Dict of total expenses
    :param s_dates: String of statement date
    """
    stats_tot = np.array(list(expenses_tot.values()))
    stats_cat = np.array(list(expenses_tot.keys()))
    explosion = [0.1] * len(list(expenses_tot.keys()))
    labels = ['{0} - ${1:1.2f}'.format(i,j) for i,j in zip(stats_cat, stats_tot)]
    patches, texts = plt.pie(stats_tot, labels=stats_cat, explode=explosion, startangle=0)
    plt.title(f'Expense Report for Statement: {s_dates[0]}\n')
    save_img = '/tmp/report.png'
    plt.legend(patches, labels, bbox_to_anchor=(1.0, 0.5), loc="center right", fontsize=10,
               bbox_transform=plt.gcf().transFigure)
    plt.subplots_adjust(left=0.2, bottom=0.1, right=0.6)
    plt.savefig(save_img)
    # plt.show()
    plt.clf()
    print(f'Report saved to {tmp_report_path}')


def send_email(expenses_tot: dict, expenses_cl: dict, s_dates: list, u_email):
    """
    This function will use the Amazon AWS Simple Email Service to send the email with expenses
    and the expense pie chart
    :param expenses_tot: Dict of total expenses
    :param expenses_cl: Dict of classified expenses
    :param s_dates: String of statement date
    :param u_email: String of user email
    """
    print(f'Fetching verified email from expense-email-verifier service')
    email_verifier_req = {"user-email": str(u_email)}
    email_verifier_resp = requests.post(url=expense_email_verifier_agw,
                                        data=json.dumps(email_verifier_req))
    if email_verifier_resp.status_code == 200:
        destinations = list()
        destinations.append(u_email)
        print(f'Email verified and proceeding with email generation')
        msg = MIMEMultipart()
        mail_title = f'Expense Report: {s_dates[0]}\n'
        msg["Subject"] = mail_title
        msg["From"] = sender_email
        msg["To"] = ",".join(destinations)
        # Set message body
        expenses_str = format_expenses(expenses_tot, expenses_cl, True)
        body = MIMEText(expenses_str)
        msg.attach(body)
        # Set the file as attachment
        print(f'Fetching report from {tmp_report_path}')
        with open(tmp_report_path, "rb") as attachment:
            part = MIMEApplication(attachment.read())
            part.add_header("Content-Disposition",
                            "attachment",
                            filename=os.path.basename(tmp_report_path))
        msg.attach(part)
        print(f'Report fetched from {tmp_report_path}')
        # Convert message to string and send
        ses_client = boto3.client('ses')
        response = ses_client.send_raw_email(
            Source = sender_email,
            Destinations = destinations,
            RawMessage = {"Data": msg.as_string()}
        )


def lambda_handler(event, context):
    try:
        event_body = json.loads(event['Records'][0]['body'])
        print(f'Incoming SQS Message: {event_body}')
        bucket = event_body['Records'][0]['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(event_body['Records'][0]['s3']['object']['key'],
                                        encoding='utf-8')
        user_email = key.split('/')[1]
        print(f'Generating report for user email: {user_email}')
        file_contents = fetch_contents(bucket, key)
        dates = parse_stmt_date(file_contents)
        expenses_all = categorize_transactions(file_contents)
        plot_expenses(expenses_all[0], dates)
        send_email(expenses_all[0], expenses_all[1], dates, user_email)
    except Exception as e:
        msg = '\nProcessing error. Check Cloudwatch logs.'
        raise Exception(msg)


if __name__ == '__main__':
    script_dir = os.path.dirname(__file__)
    rel_path = '../events/test-sqs-event.json'
    abs_file_path = os.path.join(script_dir, rel_path)
    with open(abs_file_path) as f:
        test_event = json.load(f)
        lambda_handler(test_event, None)

