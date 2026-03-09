"""
Classifier Service — turns raw URLs/Titles into structured knowledge events.
In production, this would use an LLM (Gemma-3) or a heavy NLP model.
For MVP, we use a high-performance keyword mapping.
"""
import re
from app.models.event import EventDepth

import re
import re
import json
import httpx
from app.models.event import EventDepth, ActivityType
from app.core.config import settings

# Fallback keywords for offline/no-key usage
KEYWORDS = {
    "react": {"tech": "React", "domain": "Frontend"},
    "typescript": {"tech": "TypeScript", "domain": "Frontend"},
    "fastapi": {"tech": "FastAPI", "domain": "Backend"},
    "python": {"tech": "Python", "domain": "Backend"},
    "docker": {"tech": "Docker", "domain": "DevOps"},
    "kubernetes": {"tech": "Kubernetes", "domain": "DevOps"},
    "sql": {"tech": "SQL", "domain": "Data"},
    "postgres": {"tech": "PostgreSQL", "domain": "Backend"},
    "pytorch": {"tech": "PyTorch", "domain": "AI/ML"},
    "tensorflow": {"tech": "TensorFlow", "domain": "AI/ML"},
    "django": {"tech": "Django", "domain": "Backend"},
    "next.js": {"tech": "Next.js", "domain": "Frontend"},
    "aws": {"tech": "AWS", "domain": "DevOps"},
}

async def classify_event(url: str, title: str) -> dict:
    """
    Dynamically classifies learning context using AI (LLM).
    Falls back to keyword matching if AI is unavailable.
    """
    if settings.OPENROUTER_API_KEY:
        try:
            return await _classify_with_ai(url, title)
        except Exception as e:
            print(f"[Classifier] AI Error: {e}. Falling back to keywords.")
    
    return _classify_with_keywords(url, title)

async def _classify_with_ai(url: str, title: str) -> dict:
    """Uses OpenRouter to classify the content dynamically."""
    prompt = f"""
    Analyze this web page that a developer is visiting:
    URL: {url}
    Title: {title}

    Identify the specific technology, the broad engineering domain, and the depth of the content.
    Also, identify the type of learning activity (READING_DOCS, WATCHING_VIDEO, CODING, BROWSING) based on the URL and title. Give an engagement_score (0.0 to 1.0) approximating the active effort required.
    Crucially, determine if this page is actually about software development/engineering. Add a boolean 'is_relevant'. Set it to false if it is entertainment, social media (non-tech), general news, or unrelated waste.
    Return ONLY a JSON object in this format:
    {{
      "is_relevant": true | false,
      "topic": "Specific concept, e.g. React Hooks",
      "technology": "Standard tech name, e.g. React",
      "domain": "Broad area, e.g. Frontend, Backend, DevOps, AI/ML, Data",
      "depth": "beginner" | "intermediate" | "advanced",
      "activity_type": "reading_docs" | "watching_video" | "coding" | "browsing",
      "engagement_score": 0.0 to 1.0,
      "confidence": 0.0 to 1.0
    }}
    """

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://devbrain.dev", # Optional
                "X-Title": "DevBrain Classifier"
            },
            json={
                "model": settings.AI_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            },
            timeout=10.0
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            data = json.loads(content)
            
            # Map string depth to Enum
            depth_map = {
                "beginner": EventDepth.BEGINNER,
                "intermediate": EventDepth.INTERMEDIATE,
                "advanced": EventDepth.ADVANCED
            }
            data["depth"] = depth_map.get(data.get("depth", "beginner"), EventDepth.BEGINNER)
            
            activity_map = {
                "reading_docs": ActivityType.READING_DOCS,
                "watching_video": ActivityType.WATCHING_VIDEO,
                "coding": ActivityType.CODING,
                "browsing": ActivityType.BROWSING
            }
            data["activity_type"] = activity_map.get(data.get("activity_type", "browsing"), ActivityType.BROWSING)
            data["engagement_score"] = float(data.get("engagement_score", 0.5))
            data["is_relevant"] = bool(data.get("is_relevant", True))
            
            return data
        else:
            raise Exception(f"API returned status {response.status_code}")

def _classify_with_keywords(url: str, title: str) -> dict:
    """Old keyword-based fallback logic."""
    text = (url + " " + title).lower()
    found_tech = "General"
    found_domain = "Engineering"
    
    for key, meta in KEYWORDS.items():
        if key in text:
            found_tech = meta["tech"]
            found_domain = meta["domain"]
            break

    depth = EventDepth.BEGINNER
    if any(k in text for k in ["advanced", "expert", "pro", "internals", "architecture"]):
        depth = EventDepth.ADVANCED
    elif any(k in text for k in ["tutorial", "howto", "guide", "learn", "basics"]):
        depth = EventDepth.INTERMEDIATE

    topic = title or "Study Session"
    if " - " in topic: topic = topic.split(" - ")[0]
    
    activity = ActivityType.BROWSING
    engagement = 0.5
    if "youtube.com/watch" in text:
        activity = ActivityType.WATCHING_VIDEO
        engagement = 0.8
    elif "docs." in text or ".dev" in text or "developer." in text:
        activity = ActivityType.READING_DOCS
        engagement = 0.7

    is_relevant = False
    if found_tech != "General" or activity != ActivityType.BROWSING or "github" in text or "stackoverflow" in text:
        is_relevant = True

    return {
        "is_relevant": is_relevant,
        "topic": topic,
        "technology": found_tech,
        "domain": found_domain,
        "depth": depth,
        "activity_type": activity,
        "engagement_score": engagement,
        "confidence": 0.7 if found_tech != "General" else 0.3
    }
