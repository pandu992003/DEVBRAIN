import json

class SnowflakeService:
    async def send_to_snowflake(self, event_data: dict):
        """
        Inserts structured JSON event into Snowflake raw_events table.
        Uses a thread pool to avoid blocking the main async loop.
        """
        # Lazy import to keep the top-level fast
        import asyncio
        from anyio import to_thread
        # Run the synchronous Snowflake DB call in a background thread
        # This keeps the FastAPI event loop free and fast
        return await to_thread.run_sync(self._execute_insert, event_data)

    def _execute_insert(self, event_data: dict):
        # Lazy import of snowflake client
        from app.services.snowflake_client import get_connection
        
        conn = None
        cursor = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            insert_query = """
            INSERT INTO raw_events (user_id, source, payload)
            SELECT %s, %s, PARSE_JSON(%s)
            """

            user_id = str(event_data.get("user_id", "unknown"))
            source = str(event_data.get("source", "browser"))
            
            cursor.execute(
                insert_query,
                (
                    user_id,
                    source,
                    json.dumps(event_data)
                )
            )
            conn.commit()
            print(f"[SnowflakeService] Stored event from source {source} in Snowflake.")
            return True
        except Exception as e:
            print(f"[SnowflakeService] Failed to store in Snowflake: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

snowflake_service = SnowflakeService()

