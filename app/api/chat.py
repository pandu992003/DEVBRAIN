"""
DevBrain Chatbot API - Interrogates the Snowflake Data Warehouse to generate LLM responses.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import httpx
from anyio import to_thread

from app.core.security import get_current_user
from app.core.config import settings
from app.api.analytics import _run_snowflake_query

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

def get_snowflake_context(user_id: str) -> str:
    """
    Retrieves user learning context exclusively from Snowflake Gold and Silver layers.
    """
    # 1. Gold Layer: Top Technologies
    tech_query = "SELECT technology, hits FROM technology_trends WHERE user_id = %s ORDER BY hits DESC LIMIT 10"
    techs = _run_snowflake_query(tech_query, (user_id,))
    
    # 2. Silver Layer: Recent Context
    recent_query = """
    SELECT topic, technology, activity_type, TO_CHAR(event_timestamp, 'YYYY-MM-DD HH24:MI:SS') as time_str
    FROM knowledge_events
    WHERE user_id = %s
    ORDER BY event_timestamp DESC
    LIMIT 10
    """
    recent_events = _run_snowflake_query(recent_query, (user_id,))
    
    context = "USER'S SNOWFLAKE LEARNING DATA:\n\n"
    context += "Top Technologies (Gold Tier):\n"
    if techs and len(techs) > 0:
        for t in techs:
            context += f"- {t.get('TECHNOLOGY', 'Unknown')}: {t.get('HITS', 0)} learning sessions\n"
    else:
        context += "- User has not logged any technologies yet.\n"
        
    context += "\nRecent Activity History (Silver Tier):\n"
    if recent_events and len(recent_events) > 0:
        for e in recent_events:
            context += f"- Studied '{e.get('TOPIC')}' ({e.get('TECHNOLOGY')}) via {e.get('ACTIVITY_TYPE')} at {e.get('TIME_STR')}\n"
    else:
        context += "- No recent learning events logged.\n"
        
    return context

@router.post("/")
async def chat_with_devbrain(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    user_context = await to_thread.run_sync(get_snowflake_context, str(current_user.id))
    
    system_prompt = f"""You are DevBrain AI, an intelligent, conversational learning assistant built for developers.
    You have direct access to the user's learning data streamed straight from the Snowflake Data Warehouse.
    
    {user_context}
    
    INSTRUCTIONS:
    - Answer the user's query intelligently based on their literal Snowflake actual learning data above.
    - Be conversational, modern, and encouraging.
    - If they ask what they should learn next, look at their Top Technologies and suggest related advanced topics.
    - DO NOT generate JSON. Return clean, formatted markdown text only.
    - Limit responses to concise, actionable paragraphs.
    """

    if not settings.OPENROUTER_API_KEY:
        return {"response": "DevBrain AI is currently offline. missing OpenRouter API Key in backend configuration."}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://devbrain.dev",
                    "X-Title": "DevBrain Chatbot"
                },
                json={
                    "model": settings.AI_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": request.message}
                    ]
                },
                timeout=20.0
            )
            response.raise_for_status()
            result = response.json()
            reply = result['choices'][0]['message']['content']
            return {"response": reply}
        except Exception as e:
            print(f"[Chatbot] Error hitting LLM: {e}")
            raise HTTPException(status_code=500, detail="DevBrain AI Failed to respond.")
