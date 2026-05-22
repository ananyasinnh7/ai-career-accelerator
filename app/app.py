from fastapi import FastAPI,HTTPException,File,UploadFile,Form,Depends
from app.db import Post ,create_db_and_tables,get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy import select

@asynccontextmanager
async def lifespan(app:FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)


@app.post("/upload")
async def upload_file(
        file: UploadFile = File(...),
        caption: str = Form(""),
        session: AsyncSession = Depends(get_async_session)
):
    post = Post(
        captions=caption,        # 👈 ✅ CHANGED to 'captions' (Plural)
        url="dummy url",
        file_type="photo",
        file_name=file.filename
    )
    session.add(post)
    await session.commit()
    await session.refresh(post)
    return post


@app.get("/feed")
async def get_feed(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Post).order_by(Post.created_at.desc()))
    posts = result.scalars().all()  # 👈 Use .scalars() for cleaner list

    posts_data = []
    for post in posts:
        posts_data.append({
            "id": str(post.id),
            "caption": post.captions,
            "url": post.url,
            "file_type": post.file_type,
            "file_name": post.file_name,
            "created_at": post.created_at.isoformat()
        })

    return {"posts": posts_data}