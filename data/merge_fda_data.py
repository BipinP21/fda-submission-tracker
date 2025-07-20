import pandas as pd
import os

# Verify openpyxl is installed
try:
    import openpyxl
except ImportError:
    print("Error: 'openpyxl' is not installed. Install it using 'pip install openpyxl'.")
    exit(1)

# Path to the current directory
data_dir = os.path.dirname(os.path.abspath(__file__))
print("Data directory:", data_dir)

try:
    # Load main files
    submissions = pd.read_csv(os.path.join(data_dir, "Submissions.txt"), sep="\t", encoding="latin1")
    applications = pd.read_csv(os.path.join(data_dir, "Applications.txt"), sep="\t", encoding="latin1")
    products = pd.read_csv(os.path.join(data_dir, "Products.txt"), sep="\t", encoding="latin1", on_bad_lines="skip")

    # Print columns and row counts for verification
    print("Submissions columns:", submissions.columns.tolist(), f"({len(submissions)} rows)")
    print("Applications columns:", applications.columns.tolist(), f"({len(applications)} rows)")
    print("Products columns:", products.columns.tolist(), f"({len(products)} rows)")

    # Keep necessary columns
    sub = submissions[["ApplNo", "SubmissionType", "SubmissionNo", "SubmissionStatus", "SubmissionStatusDate", "ReviewPriority"]].copy()
    apps = applications[["ApplNo", "SponsorName"]].copy()
    prods = products[["ApplNo", "Form", "Strength", "DrugName"]].copy()

    # Rename for clarity
    sub.rename(columns={
        "ApplNo": "Application_No",
        "SubmissionType": "Submission_Type",
        "SubmissionNo": "Submission_No",
        "SubmissionStatus": "Status",
        "SubmissionStatusDate": "Submission_Date"
    }, inplace=True)

    apps.rename(columns={
        "ApplNo": "Application_No",
        "SponsorName": "Sponsor"
    }, inplace=True)

    prods.rename(columns={
        "ApplNo": "Application_No"
    }, inplace=True)

    # Ensure consistent data types for merging
    sub["Application_No"] = sub["Application_No"].astype(str)
    apps["Application_No"] = apps["Application_No"].astype(str)
    prods["Application_No"] = prods["Application_No"].astype(str)

    # Aggregate products by Application_No
    prods = prods.groupby("Application_No").agg({
        "Form": lambda x: ", ".join(x.dropna()),
        "Strength": lambda x: ", ".join(x.dropna()),
        "DrugName": lambda x: ", ".join(x.dropna())
    }).reset_index()

    # Check for duplicates
    print("Unique Application_No in Submissions:", sub["Application_No"].nunique())
    print("Unique Application_No in Applications:", apps["Application_No"].nunique())
    print("Unique Application_No in Products:", prods["Application_No"].nunique())
    print("Duplicate Application_No in Applications:", apps["Application_No"].duplicated().sum())
    print("Duplicate Application_No in Products:", prods["Application_No"].duplicated().sum())

    # Merge step-by-step
    df = sub.merge(apps, on="Application_No", how="left")
    print("Rows after merging with Applications:", len(df))
    df = df.merge(prods, on="Application_No", how="left")
    print("Merged rows:", len(df))

    # Clean submission type and status codes
    submission_type_map = {
        "AP": "Abbreviated NDA", "TP": "Therapeutic",
        "ORIG": "Original", "SUPPL": "Supplemental"
    }
    df["Submission_Type"] = df["Submission_Type"].replace(submission_type_map)
    print("Unique Submission Types:", df["Submission_Type"].unique().tolist())

    # Clean Form column, handling missing values
    if "Form" in df.columns:
        df["Form"] = df["Form"].fillna("").str.replace(";", " / ", regex=False)

    # Save to Excel
    output_path = os.path.join(data_dir, "fda_submissions_merged.xlsx")
    print("Output path:", output_path)
    df.to_excel(output_path, index=False)
    print(f"✅ Cleaned and saved to {output_path}")

except FileNotFoundError as e:
    print(f"Error: File not found - {e}")
except pd.errors.ParserError as e:
    print(f"Error: Parsing issue - {e}")
except KeyError as e:
    print(f"Error: Column not found - {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
