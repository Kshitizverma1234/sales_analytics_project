# Sales Analytics & Data Pipeline - Demo

This project contains a small synthetic dataset and scripts to demonstrate a complete ETL -> SQL -> Dashboard workflow.

## What is included
- `data/` - sample CSV files: customers.csv, products.csv, orders.csv, order_items.csv, shipments.csv
- `sql/schema.sql` - PostgreSQL DDL to create the schema
- `etl_pipeline.py` - ETL script (pandas + SQLAlchemy) to load CSVs into the database
- `app.py` - Streamlit dashboard (simple) to visualize monthly revenue and top products
- `README.md` - this file

## Quick start (run on your machine)

### 1) Install prerequisites
- Python 3.8+
- PostgreSQL (or use any Postgres-compatible DB)
- (Optional) virtualenv or venv
- From a terminal / CMD:
```bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate       # Windows (PowerShell: .\\venv\\Scripts\\Activate.ps1)
pip install --upgrade pip
pip install pandas sqlalchemy psycopg2-binary streamlit
```

### 2) Create a Postgres database and run schema
- Create DB (example commands):
```bash
# Linux / macOS
sudo -u postgres psql
CREATE DATABASE salesdb;
CREATE USER demo_user WITH PASSWORD 'demo_pass';
GRANT ALL PRIVILEGES ON DATABASE salesdb TO demo_user;
\q
# then from terminal:
psql -U demo_user -d salesdb -h localhost -f sql/schema.sql
```

- Or use pgAdmin / any GUI to run `sql/schema.sql` against your database.

### 3) Configure DB connection
- Set the environment variable `DB_URL` used by `etl_pipeline.py` and `app.py` (SQLAlchemy URL):
  Example for PostgreSQL (replace user/password/host/db):
```
export DB_URL="postgresql+psycopg2://demo_user:demo_pass@localhost:5432/salesdb"   # Linux/macOS
setx DB_URL "postgresql+psycopg2://demo_user:demo_pass@localhost:5432/salesdb"    # Windows (restart terminal)
```

### 4) Run the ETL to load sample data
```bash
python etl_pipeline.py
```

Fix any errors printed (typically missing DB connection or schema not created).

### 5) Run the Streamlit dashboard
```bash
streamlit run app.py
```

Open the URL shown in the terminal (usually http://localhost:8501).

## Notes & troubleshooting
- If ETL aborts with missing references, ensure `sql/schema.sql` has been applied and DB_URL is correct.
- For demo/testing, you can also import CSVs directly in your DB client tools (pgAdmin, DBeaver) to inspect data before running ETL.

Enjoy!

