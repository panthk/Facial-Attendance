import os
import time
import gspread
from datetime import datetime

def setup_gspread():
    gc = gspread.service_account(filename="gspread json/facialattendance-422303-6c0203fda5e3.json")
    return gc

def get_names_from_folder(folder_path):
    names = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".png"):
            name = os.path.splitext(filename)[0]
            names.append(name)
    return names

def get_names_from_sheet(sheet, column_index=1):
    names = sheet.col_values(column_index)
    return names

def retry_on_rate_limit(func, *args, **kwargs):
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            result = func(*args, **kwargs)
            return result
        except gspread.exceptions.APIError as e:
            if e.response.status_code == 429:
                wait_time = 60
                print(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                retry_count += 1
            else:
                raise
    raise Exception("Maximum retries exceeded")

def check_and_update_sheet(folder_path, sheet, column_index=1):
    names_in_folder = sorted(get_names_from_folder(folder_path))
    names_in_sheet = get_names_from_sheet(sheet, column_index)
    
    if len(names_in_sheet) <= 1:
        for i, name in enumerate(names_in_folder, start=2):
            retry_on_rate_limit(sheet.update_cell, i, column_index, name)
        print("Google Sheet was empty. Populated with names from the folder.")
    else:
        names_in_sheet = names_in_sheet[1:]
        
        missing_names = [name for name in names_in_folder if name not in names_in_sheet]
        if missing_names:
            print("Missing names in Google Sheet:", missing_names)
            all_names = sorted(set(names_in_sheet + missing_names))
            for i, name in enumerate(all_names, start=2):
                retry_on_rate_limit(sheet.update_cell, i, column_index, name)
        else:
            print("All names are present in the Google Sheet.")

def mark_attendance(sheet, name):
    # today = datetime.now().strftime("%B %d, %Y").replace(", 2024", "")
    today = datetime.now().strftime("%B %d, %Y")
    cell = sheet.find(today)

    if cell:
        date_col = cell.col
        name_cell = sheet.find(name)
        
        if name_cell:
            row = name_cell.row
            current_value = sheet.cell(row, date_col).value
            
            if current_value == 'x':
                print(f"Attendance for {name} on {today} has already been marked.")
            else:
                retry_on_rate_limit(sheet.update_cell, row, date_col, 'x')
                print(f"Marked attendance for {name} on {today}")
        else:
            print(f"Name {name} not found in the sheet.")
    else:
        print(f"Date {today} not found in the sheet.")

def main():
    folder_path = "known_faces"
    client = setup_gspread()
    sheet_name = "gsheets test123"
    worksheet_index = 0
    sheet = client.open(sheet_name).get_worksheet(worksheet_index)
    check_and_update_sheet(folder_path, sheet)
    
    names_to_mark = ["Alice", "Bob"]
    for name in names_to_mark:
        mark_attendance(sheet, name)

if __name__ == "__main__":
    main()