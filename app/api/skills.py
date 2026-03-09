"""
Skill Graph API — query skill scores and gaps.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.skill import SkillGraphResponse, DomainNode, TechNode, GapsResponse, GapAnalysis
from app.services.skill_service import get_user_skills, get_skill_gaps

router = APIRouter()


@router.get("/", response_model=SkillGraphResponse)
async def get_skill_graph(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Returns the full skill graph for the authenticated user,
    grouped by domain → technology.
    """
    skills = await get_user_skills(db, current_user.id)

    # Group by domain
    domains_map: dict[str, list] = {}
    for skill in skills:
        domains_map.setdefault(skill.domain, []).append(skill)

    domain_nodes = []
    total_score = 0.0

    for domain, domain_skills in domains_map.items():
        tech_nodes = [
            TechNode(
                technology=s.technology,
                score=s.score,
                level=s.level,
                event_count=s.event_count,
                last_activity=s.last_activity,
            )
            for s in domain_skills
        ]
        domain_score = sum(s.score for s in domain_skills) / len(domain_skills)
        total_score += domain_score
        domain_nodes.append(
            DomainNode(domain=domain, technologies=tech_nodes, domain_score=domain_score)
        )

    overall_score = (total_score / len(domain_nodes)) if domain_nodes else 0.0

    return SkillGraphResponse(
        domains=domain_nodes,
        total_skills=len(skills),
        overall_score=round(overall_score, 1),
    )


@router.get("/gaps", response_model=GapsResponse)
async def get_gaps(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Returns the user's identified skill gaps with recommended topics.
    """
    raw_gaps = await get_skill_gaps(db, current_user.id)
    gaps = [GapAnalysis(**g) for g in raw_gaps]
    return GapsResponse(gaps=gaps, total_gaps=len(gaps))
