"""
Snowflake Analytics API — executes heavy aggregations directly against Snowflake.
"""
from fastapi import APIRouter, Depends, HTTPException
from anyio import to_thread

from app.core.security import get_current_user

router = APIRouter()

def _run_snowflake_query(query: str, params: tuple):
    from app.services.snowflake_client import get_connection
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        # Fetch dicts
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results
    except Exception as e:
        print(f"[Snowflake Analytics] Error: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@router.get("/learning-activity")
async def get_learning_activity(current_user: dict = Depends(get_current_user)):
    """
    Returns daily learning counts from Snowflake.
    """
    query = """
    SELECT 
        day AS DAY,
        learning_events AS LEARNING_EVENTS
    FROM learning_activity_daily
    WHERE user_id = %s
    ORDER BY day NULLS LAST
    """
    results = await to_thread.run_sync(_run_snowflake_query, query, (str(current_user.id),))
    if results is None:
        raise HTTPException(status_code=500, detail="Failed to run Snowflake query")
    return {"activity": results}

@router.get("/trending-technologies")
async def get_trending_technologies(current_user: dict = Depends(get_current_user)):
    """
    Returns top 5 technologies learned recently from Snowflake.
    """
    query = """
    SELECT 
        technology AS TECHNOLOGY,
        hits AS HITS
    FROM technology_trends
    WHERE user_id = %s
    ORDER BY hits DESC
    LIMIT 5
    """
    results = await to_thread.run_sync(_run_snowflake_query, query, (str(current_user.id),))
    if results is None:
        raise HTTPException(status_code=500, detail="Failed to run Snowflake query")
    return {"trending": results}

@router.get("/learning-velocity")
async def get_learning_velocity(current_user: dict = Depends(get_current_user)):
    """
    Returns activity split by Activity Type.
    """
    query = """
    SELECT 
        activity AS ACTIVITY,
        hits AS HITS
    FROM learning_velocity
    WHERE user_id = %s
    ORDER BY hits DESC
    """
    results = await to_thread.run_sync(_run_snowflake_query, query, (str(current_user.id),))
    if results is None:
        raise HTTPException(status_code=500, detail="Failed to run Snowflake query")
    return {"velocity": results}
