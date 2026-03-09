from app.services.snowflake_client import get_connection
import sys

def test_conn():
    print("Testing Snowflake connection...")
    try:
        conn = get_connection()
        ctx = conn.cursor().execute("SELECT CURRENT_VERSION()")
        one_row = ctx.fetchone()
        print(f"Success! Snowflake version: {one_row[0]}")
        conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_conn()
