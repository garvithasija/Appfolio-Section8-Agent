import pandas as pd
from datetime import datetime

# Sample applicant data
data = {
    'ApplicantFirstName': ['John', 'Jane', 'Michael', 'Sarah', 'David'],
    'ApplicantLastName': ['Smith', 'Doe', 'Johnson', 'Williams', 'Brown'],
    'DOB': ['1985-03-15', '1990-07-22', '1982-11-08', '1995-01-30', '1988-09-12'],
    'Email': [
        'john.smith@email.com',
        'jane.doe@email.com', 
        'm.johnson@email.com',
        's.williams@email.com',
        'd.brown@email.com'
    ],
    'Phone': ['555-0101', '555-0102', '555-0103', '555-0104', '555-0105'],
    'Address': [
        '123 Main St',
        '456 Oak Ave', 
        '789 Pine Rd',
        '321 Elm St',
        '654 Maple Dr'
    ],
    'City': ['Springfield', 'Chicago', 'Peoria', 'Rockford', 'Aurora'],
    'State': ['IL', 'IL', 'IL', 'IL', 'IL'],
    'ZipCode': ['62701', '60601', '61602', '61101', '60502'],
    'AnnualIncome': [35000, 42000, 28000, 38000, 45000],
    'HouseholdSize': [3, 2, 4, 1, 5]
}

# Create DataFrame
df = pd.DataFrame(data)

# Save to Excel
df.to_excel('example_applicants.xlsx', index=False)
print("Sample Excel file created: example_applicants.xlsx")
print(f"Contains {len(df)} sample applicant records")