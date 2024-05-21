import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
from gsheets import retry_on_rate_limit

def validate_date_range(date_range):
    try:
        start_date, end_date = date_range.split(' to ')
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        if start_date > end_date:
            return None, None, "Start date cannot be after end date."
        return start_date, end_date, None
    except ValueError:
        return None, None, "Invalid date format. Please use YYYY-MM-DD to YYYY-MM-DD."

def get_weekends_in_range(start_date, end_date):
    current_date = start_date
    weekends = []
    while current_date <= end_date:
        if current_date.weekday() == 5:  # Saturday
            weekend = [current_date, current_date + timedelta(days=1)]
            weekends.append(weekend)
        current_date += timedelta(days=1)
    return weekends

def format_weekends(weekends):
    formatted_weekends = []
    for weekend in weekends:
        formatted_weekends.append(f"{weekend[0].strftime('%b')} {weekend[0].day}, {weekend[0].year}")
        formatted_weekends.append(f"{weekend[1].strftime('%b')} {weekend[1].day}, {weekend[1].year}")
        formatted_weekends.append('')  # Blank cell after each weekend
    return formatted_weekends

def populate_dates(sheet, date_range):
    while True:
        start_date, end_date, error = validate_date_range(date_range)
        if error:
            print(error)
            date_range = input("Enter the date range (YYYY-MM-DD to YYYY-MM-DD): ")
            continue
        break

    weekends = get_weekends_in_range(start_date, end_date)
    formatted_weekends = format_weekends(weekends)
    formatted_weekends.insert(0, '')  # Ensure the list starts with an empty cell

    cell_list = sheet.range(1, 1, 1, len(formatted_weekends))
    for cell, date in zip(cell_list, formatted_weekends):
        cell.value = date
    retry_on_rate_limit(sheet.update_cells, cell_list)

# Setup Google Sheets connection
def connect_to_google_sheets(credentials_file, sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).sheet1
    return sheet

def main():
    # Connect to Google Sheets
    credentials_file = 'gspread json/facialattendance-422303-6c0203fda5e3.json'  # Update this path
    sheet_name = 'gsheets test123'  # Update this with your sheet name
    sheet = connect_to_google_sheets(credentials_file, sheet_name)

    # Check if the first row is already filled
    first_row = sheet.row_values(1)
    if first_row:
        print("The first row is already filled.")
        return

    # Prompt user for date range
    while True:
        date_range = input("Enter the date range (YYYY-MM-DD to YYYY-MM-DD): ")
        start_date, end_date, error = validate_date_range(date_range)
        if error:
            print(error)
            continue
        break

    # Get and format weekends
    weekends = get_weekends_in_range(start_date, end_date)
    formatted_weekends = format_weekends(weekends)

    # Ensure the list starts with an empty cell for the first cell in the row
    formatted_weekends.insert(0, '')

    # Populate the first row with weekends
    cell_list = sheet.range(1, 1, 1, len(formatted_weekends))
    for cell, date in zip(cell_list, formatted_weekends):
        cell.value = date
    sheet.update_cells(cell_list)

    print("The first row has been populated with the weekends in the specified date range.")

if __name__ == '__main__':
    main()