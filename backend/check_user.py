import asyncio
import sys
sys.path.insert(0, '.')
from app.core.database import async_session_factory
from sqlalchemy import select
from app.models.user import User

async def check():
    async with async_session_factory() as db:
        r = await db.execute(select(User).where(User.email == 'test@enerji.com'))
        u = r.scalar_one_or_none()
        if u:
            print(f'Kullanici bulundu: id={u.id} email={u.email} is_active={u.is_active}')
        else:
            print('Kullanici bulunamadi - seed_data.py calistirilmamis')
asyncio.run(check())
