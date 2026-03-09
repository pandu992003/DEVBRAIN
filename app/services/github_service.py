"""
GitHub Service — Synchronizes repository activity and languages.
Analyzes repositories to create Knowledge Events.
"""
import httpx
from datetime import datetime
from app.models.event import EventSource, EventDepth
from app.schemas.event import EventCreate
from app.services.event_service import create_event
from app.services.skill_service import rebuild_skill_graph

async def sync_github_repos(db, user_id, github_token):
    """
    Fetches user's public repos and creates knowledge events based on languages.
    """
    url = "https://api.github.com/user/repos?sort=updated&per_page=10"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            return {"error": "Failed to fetch GitHub data"}

        repos = response.json()
        events_created = 0

        for repo in repos:
            lang = repo.get("language")
            if not lang: continue
            
            # Map GitHub language to normalized topic
            # Note: In a full app, we would also fetch the specific languages breakdown
            
            event_data = EventCreate(
                topic=f"Repo: {repo['name']}",
                technology=lang,
                domain=_map_language_to_domain(lang),
                source=EventSource.GITHUB,
                source_url=repo["html_url"],
                source_title=repo["description"] or repo["name"],
                depth=EventDepth.INTERMEDIATE,
                confidence_score=0.9 # High confidence because it's actual code
            )

            await create_event(db, user_id, event_data)
            events_created += 1

        if events_created > 0:
            await rebuild_skill_graph(db, user_id)
            
        return {"events_synced": events_created}

def _map_language_to_domain(lang):
    mapping = {
        "Python": "Backend",
        "JavaScript": "Frontend",
        "TypeScript": "Frontend",
        "Go": "Backend",
        "Rust": "Backend",
        "HTML": "Frontend",
        "CSS": "Frontend",
        "Shell": "DevOps",
        "Jupyter Notebook": "AI/ML",
        "Java": "Backend",
        "Kotlin": "Mobile",
        "Swift": "Mobile"
    }
    return mapping.get(lang, "Engineering")
