
import os
import sys
import asyncio
import psycopg2
from psycopg2.extras import RealDictConnection
import psycopg2.pool

# Add current dir to sys.path
sys.path.append(os.getcwd())

async def test_db_concurrency():
    from data.database import init_pool, get_db_connection
    
    print("Initializing pool...")
    # Mocking environment variables if not set, but they should be there
    init_pool()
    
    async def task(i):
        print(f"Task {i} starting...")
        try:
            conn = get_db_connection()
            print(f"Task {i} got connection: {type(conn)}")
            with conn.cursor() as cur:
                cur.execute("SELECT 1 as val")
                res = cur.fetchone()
                print(f"Task {i} result: {res}")
            conn.close()
            print(f"Task {i} connection closed.")
        except Exception as e:
            print(f"Task {i} error: {e}")

    print("Running 5 tasks in parallel...")
    import asyncio
    # Since get_db_connection is currently sync but intended for to_thread usage in app
    await asyncio.gather(*(asyncio.to_thread(task, i) for i in range(5)))
    print("Diagnostic complete.")

if __name__ == "__main__":
    asyncio.run(test_db_concurrency())
