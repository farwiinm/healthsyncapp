import psycopg2
import boto3
import pandas as pd
from io import StringIO
from sqlalchemy import create_engine

# PostgreSQL connection details
pg_conn = psycopg2.connect(
    dbname="healthsync",
    user="healthsync_user",
    password="password123",
    host="127.0.0.1",
    port="5432"
)

# Query to extract data
query = "SELECT * FROM patients"

# Redshift details
redshift_host = "healthsync-cluster.c75mbagvrmue.us-east-2.redshift.amazonaws.com"
redshift_port = "5439"
redshift_database = "dev"
redshift_user = "admin"
redshift_password = "Healthsync123!"
redshift_table = "patients"

# S3 details
s3_bucket = "healthsync-staging-data"
s3_file_path = "staging/patients.csv"
aws_region = "us-east-2"

# AWS boto3 client
s3_client = boto3.client('s3', region_name=aws_region)

# Step 1: Extract data from PostgreSQL
def extract_data():
    print("Extracting data from PostgreSQL...")
    df = pd.read_sql(query, pg_conn)
    return df

# Step 2: Load data to S3
def load_to_s3(df):
    print("Loading data to S3...")
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    s3_client.put_object(Bucket=s3_bucket, Key=s3_file_path, Body=csv_buffer.getvalue())

# Step 3: Load data to Redshift
def load_to_redshift():
    try:
        print("Loading data to Redshift...")
        copy_query = f"""
            COPY {redshift_table}
            FROM 's3://{s3_bucket}/{s3_file_path}'
            IAM_ROLE 'arn:aws:iam::640168457618:role/RedShiftS3ReadRole'
            REGION '{aws_region}'
            FORMAT AS CSV
            IGNOREHEADER 1;
        """
        # Use the correct connection string
        engine = create_engine(f'redshift+psycopg2://{redshift_user}:{redshift_password}@{redshift_host}:{redshift_port}/{redshift_database}')
        with engine.connect() as connection:
            connection.execute(copy_query)
        print("Data successfully loaded into Redshift.")
    except Exception as e:
        print(f"Error loading data into Redshift: {e}")
        raise

# Step 4: Orchestrate the ETL process
def run_etl():
    df = extract_data()
    load_to_s3(df)
    load_to_redshift()
    print("ETL process completed.")

if __name__ == "__main__":
    run_etl()
