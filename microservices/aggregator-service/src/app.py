import psycopg2
import boto3
import pandas as pd
from io import StringIO

# PostgreSQL connection details
PG_HOST = '10.102.37.163'
PG_PORT = '5432'
PG_DATABASE = 'healthsync'
PG_USER = 'healthsync_user'
PG_PASSWORD = 'password123'

# Redshift connection details
REDSHIFT_CLUSTER_ID = 'healthsync-cluster'
REDSHIFT_DB = 'dev'
REDSHIFT_USER = 'admin'
REDSHIFT_PASSWORD = 'Healthsync123!'
REDSHIFT_REGION = 'us-east-2'
IAM_ROLE_ARN = 'arn:aws:iam::640168457618:role/RedShiftS3ReadRole'

# S3 bucket and path details
S3_BUCKET = 'healthsync-staging-data'

def fetch_data_from_postgres():
    conn = None
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD
        )
        cursor = conn.cursor()

        # Aggregation 1: Number of appointments per doctor
        cursor.execute("""
            SELECT doctor_id, COUNT(*) AS appointment_count
            FROM appointments
            GROUP BY doctor_id;
        """)
        appointments_per_doctor = pd.DataFrame(cursor.fetchall(), columns=['doctor_id', 'appointment_count'])

        # Aggregation 2: Frequency of appointments over time
        cursor.execute("""
            SELECT appointment_date, COUNT(*) AS appointment_count
            FROM appointments
            GROUP BY appointment_date
            ORDER BY appointment_date;
        """)
        appointments_over_time = pd.DataFrame(cursor.fetchall(), columns=['appointment_date', 'appointment_count'])

        # Aggregation 3: Common symptoms and conditions by specialty
        cursor.execute("""
            SELECT d.specialty, a.reason, COUNT(*) AS frequency
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            WHERE a.reason IS NOT NULL
            GROUP BY d.specialty, a.reason
            ORDER BY frequency DESC;
        """)
        common_conditions_by_specialty = pd.DataFrame(cursor.fetchall(), columns=['specialty', 'condition', 'frequency'])

        return {
            "appointments_per_doctor": appointments_per_doctor,
            "appointments_over_time": appointments_over_time,
            "common_conditions_by_specialty": common_conditions_by_specialty
        }
    except psycopg2.OperationalError as oe:
        print(f"Operational error connecting to PostgreSQL: {oe}")
        return {}
    except Exception as e:
        print(f"Error fetching data from PostgreSQL: {e}")
        return {}
    finally:
        if conn:
            try:
                conn.close()
                print("PostgreSQL connection closed.")
            except Exception as close_err:
                print(f"Error closing PostgreSQL connection: {close_err}")

def upload_to_s3(dataframe, metric_name):
    try:
        csv_buffer = StringIO()
        dataframe.to_csv(csv_buffer, index=False)

        s3_key = f"staging/{metric_name}.csv"
        s3_client = boto3.client('s3', region_name=REDSHIFT_REGION)
        s3_client.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=csv_buffer.getvalue())

        print(f"Data uploaded to S3: s3://{S3_BUCKET}/{s3_key}")
        return s3_key
    except Exception as e:
        print(f"Error uploading data to S3 for {metric_name}: {e}")
        return None

def upload_to_redshift(s3_key, table_name):
    try:
        session = boto3.Session(region_name=REDSHIFT_REGION)
        client = session.client('redshift-data')

        sql = f"""
        COPY {table_name}
        FROM 's3://{S3_BUCKET}/{s3_key}'
        IAM_ROLE '{IAM_ROLE_ARN}'
        CSV
        IGNOREHEADER 1;
        """
        response = client.execute_statement(
            ClusterIdentifier=REDSHIFT_CLUSTER_ID,
            Database=REDSHIFT_DB,
            DbUser=REDSHIFT_USER,
            Sql=sql
        )
        print(f"Data uploaded to Redshift table {table_name}: {response}")
    except Exception as e:
        print(f"Error uploading to Redshift table {table_name}: {e}")

def aggregate_and_store():
    metrics = fetch_data_from_postgres()
    if not metrics:
        print("No data to process.")
        return

    for metric_name, dataframe in metrics.items():
        if not dataframe.empty:
            s3_key = upload_to_s3(dataframe, metric_name)
            if s3_key:
                upload_to_redshift(s3_key, metric_name)
        else:
            print(f"No data available for {metric_name}")

if __name__ == "__main__":
    aggregate_and_store()
