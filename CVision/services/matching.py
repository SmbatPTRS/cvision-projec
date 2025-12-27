from db.db import pool

def find_best_match(cv_embedding):
    conn = pool.getconn()
    
    cursor = conn.cursor()
    
    query = """
            SELECT 
                e.job_id,
                1 - (e.embedding <=> %s) AS similarity,
                j.title,
                j.url
            FROM jobs_embeddings e
            JOIN jobs j
                ON e.job_id = j.id
            ORDER BY similarity DESC
            LIMIT 10;
    """
    
    
    vector_str = "[" + ",".join(str(float(x)) for x in cv_embedding) + "]"
    
    cursor.execute(query, (vector_str,))
    
    results = cursor.fetchall()
    
    print(results)
    pool.putconn(conn)
    return results


    return rows