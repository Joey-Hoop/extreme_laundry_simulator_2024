import csv
import re
from datetime import datetime, timedelta
from atlassian import Jira
import traceback2 as traceback
from colorama import Fore, Style, init
import concurrent.futures

# Initialize colorama
init()

def safe_str(obj):
    try:
        return str(obj)
    except UnicodeEncodeError:
        return obj.encode('ascii', 'replace').decode('ascii')

def convert_time_to_seconds(time_str):
    # A work day is 8 hours and a work week is 5 days
    time_units = {'w': 5 * 8 * 3600, 'd': 8 * 3600, 'h': 3600, 'm': 60, 's': 1}
    total_seconds = 0
    parts = re.findall(r'(\d+)([wdhms])', time_str)
    for amount, unit in parts:
        total_seconds += int(amount) * time_units[unit]
    return total_seconds

def initialize_jira_connection(url, username, token):
    return Jira(url=url, username=username, token=token)  # !! IMPORTANT !! --- change to token=token when using with SE2 --- (and password=token for Jira Cloud)

def fetch_latest_ticket(jira, project_key):
    jql_query = f'project = {project_key} ORDER BY created DESC'
    try:
        tickets = jira.jql(jql_query, limit=1)['issues']
        if tickets:
            return tickets[0]
        else:
            print(Style.BRIGHT + Fore.YELLOW + "No tickets found in the project." + Style.RESET_ALL)
            return None
    except Exception as e:
        print(Style.BRIGHT + Fore.RED + f"Error fetching tickets: {e}" + Style.RESET_ALL)
        traceback.print_exc()
        return None

def fetch_issues_concurrently(jira, project_key, start_range, end_range, max_workers=10):
    issues_list = []

    def fetch_issue(issue_key):
        try:
            issue = jira.issue(issue_key, expand='changelog')
            print(issue['key'], issue['fields']['summary'])
            return issue
        except Exception as e:
            print(Style.BRIGHT + Fore.YELLOW + f"Could not fetch issue {issue_key}. Error: {e}" + Style.RESET_ALL)
            # traceback.print_exc()
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_issue_key = {executor.submit(fetch_issue, f"{project_key}-{i}"): f"{project_key}-{i}" for i in range(start_range, end_range + 1)}
        for future in concurrent.futures.as_completed(future_to_issue_key):
            issue = future.result()
            if issue:
                issues_list.append(issue)

    # Sort the issues_list based on the issue key
    issues_list.sort(key=lambda x: x['key'])

    # ---- DEBUG ----
    print("\n\n------- DEBUG VERBOSE OUTPUT -------\n\n")
    for issue in issues_list:
        issue_key = issue.get('key', 'No Key Found')
        summary = issue['fields'].get('summary', 'No Summary Found')
        status = issue['fields']['status'].get('name', 'No Status Found')
        # Attempt to print some changelog information for debugging
        if 'changelog' in issue:
            print(f"Issue Key: {issue_key}, Summary: {summary}, Status: {status}, Changelog Entries: {len(issue['changelog']['histories'])}")
        else:
            print(f"Issue Key: {issue_key}, Summary: {summary}, Status: {status}, Changelog: Not Retrieved")
    # ---- END DEBUG ----

    return issues_list

def calculate_working_hours(start_date, end_date):
    weekdays = 0
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Monday to Friday
            weekdays += 1
        current_date += timedelta(days=1)
    return weekdays * 8  # Assuming 8 working hours per day

def write_issues_to_csv(jira, issues_list, filename):

    max_labels = 0
    for issue in issues_list:
        labels = issue['fields'].get('labels', [])
        if len(labels) > max_labels:
            max_labels = len(labels)

    print(f"Starting to write data to {filename}...")
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        # Headers for the CSV file
        headers = [
            'Sort_ID', 'Issue Key', 'Summary', 'Status', 'Priority', 'Labels', 'Worklog Comment', 'Author',
            'Time Spent', 'Time Spent Converted', 'Work Hours', 'Work Days', 'Work Weeks',
            'Work Months', 'Work Years', 'Inactive', 'Worklog Created', 'FirstWorkLogTimeDate', 'Data Extracted Time',
            'Created', 'Done Status Set On', 'Done Completion Seconds', 'Done Completion Hours',
            'Closed Status Set On', 'Closed Completion Seconds', 'Closed Completion Hours',
            'New_Completion_Interval_Seconds', 'New_Completion_Interval_Work_Hours',
            'FaultyNCI', 'WORKLOGS_EXIST',  # Add the new column
            'Ready for Documentation', 'In Documentation', 'Doc Review',
            'Ready for Development', 'In Development', 'Development Review',
            'Ready for Test', 'In Test',
            'Ready for Integration', 'In Integration',
            'Ready for Cyber', 'In Cyber', 'Cyber Review',
            'Done',
            'Ready for ERB Review', 'Ready for CCB Review', 'Ready for Release'
        ]

        # Append label headers
        label_headers = [f'Label {i+1}' for i in range(max_labels)]
        headers.extend(label_headers)

        # Append the Complexity header
        headers.append('Complexity')

        # Append the DEBUG_FirstWorklogTimestamp and DEBUG_DoneTimestamp headers
        headers.append('DEBUG_FirstWorklogTimestamp')
        headers.append('DEBUG_DoneTimestamp')

        print(f"\nStrap in, here we go...\n")

        csv_writer.writerow(headers)
        print(f"\nCSV Headers: {headers}\n")

        rows = []  # Create a list to store all the rows

        for index, issue in enumerate(issues_list, start=1):
            print(f"\nProcessing issue {issue['key']}...\n")
            sort_id = str(index).zfill(8)  # Pad the sort_id with leading zeros to ensure a consistent length
            issue_key = issue['key']
            summary = issue['fields']['summary']
            status = issue['fields']['status']['name']
            # Extract priority information, assuming it's stored under 'priority' in the issue fields
            priority = issue['fields'].get('priority', {}).get('name', 'N/A')  # Default to 'N/A' if not available
            labels = ', '.join(issue['fields'].get('labels', []))
            created = issue['fields']['created']
            done_status_set_on = ''  # Initialize before use
            closed_status_set_on = ''  # Initialize before use

            # Extract the Complexity field
            complexity_data = issue['fields'].get('customfield_13301', {})
            complexity = complexity_data.get('value', 'N/A') if isinstance(complexity_data, dict) else 'N/A'

            # Calculate the 'Completion' time in seconds for 'Done' and 'Closed' statuses
            created_datetime = datetime.strptime(created, '%Y-%m-%dT%H:%M:%S.%f%z').astimezone()
            done_completion_seconds = 0  # Initialize as 0 for issues that aren't done
            closed_completion_seconds = 0  # Initialize as 0 for issues that aren't closed

            first_worklog_created = None
            first_worklog_timestamp = 0  # Initialize to 0
            done_timestamp = 0  # Initialize to 0

            status_timestamps = {
                'Ready for Documentation': '',
                'In Documentation': '',
                'Doc Review': '',
                'Ready for Development': '',
                'In Development': '',
                'Development Review': '',
                'Ready for Test': '',
                'In Test': '',
                'Ready for Integration': '',
                'In Integration': '',
                'Ready for Cyber': '',
                'In Cyber': '',
                'Cyber Review': '',
                'Done': '',
                'Ready for ERB Review': '',
                'Ready for CCB Review': '',
                'Ready for Release': ''
            }
            if 'changelog' in issue:
                for history in issue['changelog'].get('histories', []):
                    for item in history.get('items', []):
                        if item.get('field') == 'status':
                            status_name = item.get('toString')
                            if status_name in status_timestamps:
                                status_timestamps[status_name] = history.get('created')
                            if status_name == 'Done' and not done_status_set_on:
                                done_status_set_on = history.get('created')
                            elif status_name == 'Closed' and not closed_status_set_on:
                                closed_status_set_on = history.get('created')
                    if done_status_set_on and closed_status_set_on:
                        break

                if done_status_set_on:
                    done_datetime = datetime.strptime(done_status_set_on, '%Y-%m-%dT%H:%M:%S.%f%z').astimezone()
                    done_completion_seconds = (done_datetime - created_datetime).total_seconds()
                    done_timestamp = int(done_datetime.timestamp())  # Convert done_datetime to Unix timestamp

                if closed_status_set_on:
                    closed_datetime = datetime.strptime(closed_status_set_on, '%Y-%m-%dT%H:%M:%S.%f%z').astimezone()
                    closed_completion_seconds = (closed_datetime - created_datetime).total_seconds()

            worklogs_response = jira.get(f"rest/api/2/issue/{issue_key}/worklog")
            worklogs = worklogs_response.get('worklogs', [])
            worklogs_exist = 'Y' if worklogs else 'N'  # Determine if worklogs exist

            if worklogs:
                first_worklog = min(worklogs, key=lambda w: w['started'])
                first_worklog_created = first_worklog['started']
                first_worklog_datetime = datetime.strptime(first_worklog_created, '%Y-%m-%dT%H:%M:%S.%f%z').astimezone()
                first_worklog_timestamp = int(first_worklog_datetime.timestamp())  # Convert first_worklog_datetime to Unix timestamp

                for worklog in worklogs:
                    comment = worklog.get('comment', "No worklog comment.")
                    author_name = worklog['author']['displayName']
                    time_spent = worklog['timeSpent']
                    worklog_created = worklog['started']

                    time_spent_seconds = convert_time_to_seconds(time_spent)
                    time_spent_hours = time_spent_seconds / 3600
                    time_spent_days = time_spent_seconds / (3600 * 8)
                    time_spent_weeks = time_spent_seconds / (3600 * 8 * 5)
                    time_spent_months = time_spent_seconds / (3600 * 160)
                    time_spent_years = time_spent_hours / (2000)

                    inactive = "Yes" if "[X]" in author_name else "No"

                    done_completion_hours = done_completion_seconds / 3600 if done_completion_seconds else 0
                    closed_completion_hours = closed_completion_seconds / 3600 if closed_completion_seconds else 0

                    new_completion_interval_seconds = 0
                    new_completion_interval_work_hours = 0
                    faulty_nci = "No"  # Initialize FaultyNCI as "No" by default

                    if first_worklog_created and done_status_set_on:
                        if first_worklog_datetime <= done_datetime:
                            new_completion_interval_seconds = (done_datetime - first_worklog_datetime).total_seconds()
                            new_completion_interval_work_hours = calculate_working_hours(first_worklog_datetime, done_datetime)
                        else:
                            faulty_nci = "Yes"  # Set FaultyNCI to "Yes" if done_datetime occurs before first_worklog_datetime

                    labels = issue['fields'].get('labels', [])
                    # Prepare label fields: Fill in labels and add empty strings for missing labels
                    label_fields = labels + [''] * (max_labels - len(labels))

                    row = [
                        sort_id, safe_str(issue_key), safe_str(summary), safe_str(status), safe_str(priority), safe_str(labels),
                        safe_str(comment), safe_str(author_name), safe_str(time_spent),
                        time_spent_seconds, time_spent_hours, time_spent_days, time_spent_weeks,
                        time_spent_months, time_spent_years, inactive, safe_str(worklog_created),
                        safe_str(first_worklog_created),  # Add the FirstWorkLogTimeDate field
                        datetime.now().isoformat(), safe_str(created), safe_str(done_status_set_on),
                        done_completion_seconds, done_completion_hours, safe_str(closed_status_set_on),
                        closed_completion_seconds, closed_completion_hours,
                        new_completion_interval_seconds, new_completion_interval_work_hours,
                        faulty_nci,  # Include the FaultyNCI value in the row data
                        worklogs_exist,  # Include the WORKLOGS_EXIST value in the row data
                        safe_str(status_timestamps['Ready for Documentation']),
                        safe_str(status_timestamps['In Documentation']),
                        safe_str(status_timestamps['Doc Review']),
                        safe_str(status_timestamps['Ready for Development']),
                        safe_str(status_timestamps['In Development']),
                        safe_str(status_timestamps['Development Review']),
                        safe_str(status_timestamps['Ready for Test']),
                        safe_str(status_timestamps['In Test']),
                        safe_str(status_timestamps['Ready for Integration']),
                        safe_str(status_timestamps['In Integration']),
                        safe_str(status_timestamps['Ready for Cyber']),
                        safe_str(status_timestamps['In Cyber']),
                        safe_str(status_timestamps['Cyber Review']),
                        safe_str(status_timestamps['Done']),
                        safe_str(status_timestamps['Ready for ERB Review']),
                        safe_str(status_timestamps['Ready for CCB Review']),
                        safe_str(status_timestamps['Ready for Release'])
                    ] + label_fields + [safe_str(complexity)]  # Append the Complexity field to the row
                    # Append the DEBUG_FirstWorklogTimestamp and DEBUG_DoneTimestamp values
                    row.append(first_worklog_timestamp)
                    row.append(done_timestamp)

                    rows.append(row)  # Append each row to the rows list

                    print(Style.BRIGHT + Fore.GREEN + f"\nWriting to CSV: {row}\n")  # Print each row as it's written

            else:
                done_completion_hours = done_completion_seconds / 3600 if done_completion_seconds else 0
                closed_completion_hours = closed_completion_seconds / 3600 if closed_completion_seconds else 0
                row = [
                    sort_id, safe_str(issue_key), safe_str(summary), safe_str(status), safe_str(priority), safe_str(labels),
                    'No worklog comment.', '', '', '', '', '', '', '', '', 'No', '',
                    '',  # Add an empty string for FirstWorkLogTimeDate when there are no worklogs
                    datetime.now().isoformat(), safe_str(created), safe_str(done_status_set_on),
                    done_completion_seconds, done_completion_hours, safe_str(closed_status_set_on),
                    closed_completion_seconds, closed_completion_hours, 0, 0,
                    'No',  # Set FaultyNCI to "No" for issues without worklogs
                    worklogs_exist,  # Include the WORKLOGS_EXIST value in the row data
                    safe_str(status_timestamps['Ready for Documentation']),
                    safe_str(status_timestamps['In Documentation']),
                    safe_str(status_timestamps['Doc Review']),
                    safe_str(status_timestamps['Ready for Development']),
                    safe_str(status_timestamps['In Development']),
                    safe_str(status_timestamps['Development Review']),
                    safe_str(status_timestamps['Ready for Test']),
                    safe_str(status_timestamps['In Test']),
                    safe_str(status_timestamps['Ready for Integration']),
                    safe_str(status_timestamps['In Integration']),
                    safe_str(status_timestamps['Ready for Cyber']),
                    safe_str(status_timestamps['In Cyber']),
                    safe_str(status_timestamps['Cyber Review']),
                    safe_str(status_timestamps['Done']),
                    safe_str(status_timestamps['Ready for ERB Review']),
                    safe_str(status_timestamps['Ready for CCB Review']),
                    safe_str(status_timestamps['Ready for Release'])
                ] + [''] * max_labels + [safe_str(complexity)]  # Append the Complexity field to the row

                # Append the DEBUG_FirstWorklogTimestamp and DEBUG_DoneTimestamp values
                row.append(0)  # Set DEBUG_FirstWorklogTimestamp to 0 for issues without worklogs
                row.append(done_timestamp)

                rows.append(row)  # Append each row to the rows list
                print(Style.BRIGHT + Fore.GREEN + f"\nWriting to CSV: {row}\n")  # Print for issues without worklogs

        # Sort the rows based on the Sort_ID column (first column) in ascending order
        sorted_rows = sorted(rows, key=lambda x: x[0])

        # Write the sorted rows to the CSV file
        csv_writer.writerows(sorted_rows)

    print(f"Data successfully written to {filename}")

def process_tickets(url, username, token, project_key, start_range, end_range):

    jira = initialize_jira_connection(url, username, token)

    print(f"DEBUG: URL = {url}")
    print(f"DEBUG: Username = {username}")
    print(f"DEBUG: Token = {token}")
    print(f"DEBUG: Project Key = {project_key}")
    print(f"DEBUG: Start Range = {start_range}")
    print(f"DEBUG: End Range = {end_range}")

    last_ticket = fetch_latest_ticket(jira, project_key)
    if last_ticket:
        print(f"DEBUG: Last Ticket = {last_ticket['key']}")

    issues_list = fetch_issues_concurrently(jira, project_key, start_range, end_range)
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'jira_data_{current_time}.csv'

    # Print bold red text
    print(Style.BRIGHT + Fore.GREEN + f"[ Creating {filename} ]")
    print(Style.BRIGHT + Fore.RED + "[ !!! THIS IS GOING TO TAKE A WHILE !!! ]" + Style.RESET_ALL)
    print(Style.BRIGHT + Fore.RED + "[ !!! -- DO NOT CLOSE THIS WINDOW -- !!! ]" + Style.RESET_ALL)

    write_issues_to_csv(jira, issues_list, filename)

    print(f"Data written to {filename}")

    return filename