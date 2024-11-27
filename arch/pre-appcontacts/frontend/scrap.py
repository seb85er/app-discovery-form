import pyexcel as pe

file_path = r"C:\Users\6703\Downloads\applications-13-17.csv"  # Replace with your cleaned CSV path

# Read the CSV file using pyexcel
sheet = pe.get_sheet(file_name=file_path)
columns = sheet.colnames

if 'app_overview_app_name' not in columns:
    print("ERROR: 'app_overview_app_name' column not found in CSV.")
else:
    for row in sheet.dict:
        app_name = row.get('app_overview_app_name', '').strip()
        if app_name:
            print(f"Valid app name: {app_name}")
        else:
            print("ERROR: Missing 'app_overview_app_name'.")
