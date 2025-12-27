from psycopg2.pool import SimpleConnectionPool
from dataclasses import asdict
from models.job_models import JobDetails
from utils.helpers import L2_normalize



DB_PARAMS = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "",# example password 123
    "host": "localhost",
    "port": "5432",
}

pool = SimpleConnectionPool(1, 10, **DB_PARAMS)


def test_connection():
    try:
        conn = pool.getconn()
        cursor = conn.cursor()

        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()[0]
        print("Connected to PostgreSQL")
        print("Database version:", db_version)

        pool.putconn(conn)

        return True
    except Exception as e:
        print("Error connecting to DB:", e)
        return False
def insert_job(job_details: JobDetails):

    # Query for jobs
    job_query = """
        INSERT INTO jobs (
            url, title, company, country, seniority, category,
            resp, req, skills, employment_term, employment_type
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        RETURNING id;
    """

    # Query for jobs_embeddings
    emb_query = """
        INSERT INTO jobs_embeddings (job_id, embedding)
        VALUES (%s, %s::vector);
    """

    # L2 Normalization of embedding
    job_details.embedding = L2_normalize(job_details.embedding)

    # Convert embedding list → PostgreSQL vector format (str)
    embedding_str = "[" + ",".join(str(float(x)) for x in job_details.embedding) + "]"

    conn = None
    try:
        conn = pool.getconn()
        cursor = conn.cursor()

        # Insert into jobs

        job_data = job_details.dict()
        job_data.pop('embedding')  # Remove embedding for now
        cursor.execute(job_query, tuple(job_data.values()))  # all except embedding

        job_id = cursor.fetchone()[0] # This is the RETURNING id

        # Insert embedding for that job_id
        cursor.execute(emb_query, (job_id, embedding_str))

        print(f"Inserted job + embedding with id = {job_id}")

        conn.commit()
        return job_id
    except Exception as e:
        print("Error inserting job:", e)
        return None
    finally:
        if conn:
            pool.putconn(conn)



