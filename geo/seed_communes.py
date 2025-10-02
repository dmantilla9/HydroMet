import numpy as np
import pandas as pd
from supabase import Client, create_client

from config import CSV_URL, SUPABASE_KEY, SUPABASE_URL

# -------------------------
# INIT SUPABASE
# -------------------------
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------
# DOWNLOAD CSV AND LOAD INTO PANDAS (ALL COLUMNS)
# -------------------------
print("Downloading data from data.gouv.fr...")
df = pd.read_csv(CSV_URL, dtype=str, index_col=False)

# Keep original column names in lowercase
df = df.rename(columns=str.lower)

# Optional: remove rows without INSEE code
if "code_insee" not in df.columns:
    raise ValueError("INSEE code column not found in the CSV")
df = df.dropna(subset=["code_insee"])

# Ensure canton_code codes are strings and remove any decimal parts //after found a error
df["canton_code"] = df["canton_code"].astype(str).str.replace(".0", "", regex=False)

# All columns are kept as-is
communes = df.copy()

# Remove the unnecessary index column if it exists
if "unnamed: 0" in communes.columns:
    communes = communes.drop(columns=["unnamed: 0"])


print(f"Total communes loaded: {len(communes)}")
print(f"Columns in dataset: {list(communes.columns)}")

# -------------------------
# INSERT IN BATCHES
# -------------------------
batch_size = 500  # avoid exceeding Supabase payload limits
communes = communes.replace({np.nan: None, np.inf: None, -np.inf: None})
rows = communes.to_dict(orient="records")

for i in range(0, len(rows), batch_size):
    batch = rows[i : i + batch_size]
    # supabase.table("dim_geo_communes").insert(batch).execute() -- Only in the first run
    supabase.table("dim_geo_communes").upsert(batch).execute()
    print(f"Inserted batch {i//batch_size + 1}")

print("✅ Full communes dataset successfully loaded into Supabase")
