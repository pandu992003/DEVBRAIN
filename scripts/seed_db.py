
import asyncio
import os
import sys

# Add the current directory to sys.path so 'app' can be found
sys.path.append(os.getcwd())

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.core.database import engine, Base
from app.models.user import User
from app.models.event import KnowledgeEvent
from app.models.skill import UserSkill
from app.core.security import hash_password

async def seed_user():
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if user already exists
        result = await session.execute(select(User).where(User.email == "testuser@devbrain.dev"))
        if result.scalar_one_or_none():
            print("User 'testuser@devbrain.dev' already exists!")
            return

        user = User(
            email="testuser@devbrain.dev",
            username="testuser",
            hashed_password=hash_password("password123"),
            full_name="Test User",
            is_active=True,
            is_verified=True
        )
        session.add(user)
        await session.commit()
        print("✅ User 'testuser@devbrain.dev' created successfully!")
        print("   Password: 'password123'")

if __name__ == "__main__":
    asyncio.run(seed_user())
