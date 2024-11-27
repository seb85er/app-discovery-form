import pandas as pd

def clean_csv(csv_file_path, output_file_path):
    df = pd.read_csv(csv_file_path)

    # List of conflict-prone fields
    conflicting_fields = ['os', 'ram', 'cpu']

    # Nullify conflict-prone fields automatically
    for field in conflicting_fields:
        if field in df.columns:
            df[field] = None

    df.to_csv(output_file_path, index=False)

if __name__ == "__main__":
    # File paths
    csv_file_path = r"C:\Users\6703\Downloads\applications11-11.csv"
    output_file_path = r"C:\Users\6703\Downloads\cleaned_applications.csv"

    clean_csv(csv_file_path, output_file_path)
    print("CSV cleaned and saved to:", output_file_path)
