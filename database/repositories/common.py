from sqlalchemy.ext.asyncio import AsyncSession


async def persist(session: AsyncSession, obj, commit: bool = True):
    if commit:
        await session.commit()
    else:
        await session.flush()
    await session.refresh(obj)
    return obj


async def finish_write(session: AsyncSession, commit: bool = True) -> None:
    if commit:
        await session.commit()
    else:
        await session.flush()
