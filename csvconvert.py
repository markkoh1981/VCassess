import pandas as pd
import json

# Read the Excel file
data = pd.read_excel("test.xlsx")

# Convert to JSON
json_data = data.to_json(orient="records")

# Save to a file
with open("output.json", "w") as f:
    json.dump(json_data, f)