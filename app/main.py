from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_404_NOT_FOUND
from typing import Annotated

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db, SessionLocal
from app import models
from app.schemas import PostCreate, PostResponse, UserCreate, UserResponse, PostUpdate, UserUpdate 


Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.on_event("startup")
def seed_db_if_empty():
    """Create a default user and posts when the database is empty."""
    db = SessionLocal()
    try:
        if db.execute(select(models.Post)).scalars().first() is None:
            user = models.User(
                username="demo",
                email="demo@example.com",
                image_file=None,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            db.add(models.Post(title="First post", content="Welcome to the blog.", user_id=user.id))
            db.add(models.Post(title="Second post", content="This is the second post.", user_id=user.id))
            db.commit()
    finally:
        db.close()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")
templates = Jinja2Templates(directory="templates")


posts: list[dict] = [
    {
        "id": 1,
        "author": "user1",
        "title": "First post",
        "content": "first content",
        "date_posted": "April 20, 2025",
    },
    {
        "id": 2,
        "author": "user2",
        "title": "Second post",
        "content": "second content",
        "date_posted": "April 21, 2025",
    },
]



## home
@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
def home(request: Request, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "home.html",
        {"posts": posts, "title": "Home"},
    )




## post_page
@app.get("/posts/{post_id}", include_in_schema=False, name="post_page")
def post_page(request: Request, post_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if post:
        title = post.title[:50]
        return templates.TemplateResponse(
            request,
            "post.html",
            {"post": post, "title": title},
        )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")




## user_posts_page
@app.get("/users/{user_id}/posts", include_in_schema=False, name="user_posts")
def user_posts_page(
    request: Request,
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    result = db.execute(select(models.Post).where(models.Post.user_id == user_id))
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "user_post.html",
        {"posts": posts, "user": user, "title": f"{user.username}'s Posts"},
    )





@app.post(
    "/api/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]): # dependency injection
    
    result = db.execute(select(models.User).where(models.User.username == user.username),)
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(

            status_code=status.HTTP_400_BAD_REQUEST,
            detail = "Username already exists",
        )


    result = db.execute(select(models.User).where(models.User.email == user.email),)
    existing_email = result.scalars().first()

    if existing_email:
        raise HTTPException(

            status_code=status.HTTP_400_BAD_REQUEST,
            detail = "Email already exists",
        )
    new_user  = models.User(

        username = user.username,
        email = user.email
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user



@app.get("/api/users/{user_id}", response_model=UserResponse) # not a list since we are returning a single post
def get_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(

        select(models.User).where(models.User.id == user_id),
    )
    user  = result.scalars().first()

    if user:
        return user

    raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail = "User not found")    



## get_user_posts
@app.get("/api/users/{user_id}/posts", response_model=list[PostResponse])
def get_user_posts(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    result = db.execute(select(models.Post).where(models.Post.user_id == user_id))
    posts = result.scalars().all()
    return posts





## update_user
@app.patch("/api/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user_update.username is not None and user_update.username != user.username:
        result = db.execute(
            select(models.User).where(models.User.username == user_update.username),
        )
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

    if user_update.email is not None and user_update.email != user.email:
        result = db.execute(
            select(models.User).where(models.User.email == user_update.email),
        )
        existing_email = result.scalars().first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    if user_update.username is not None:
        user.username = user_update.username
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.image_file is not None:
        user.image_file = user_update.image_file

    db.commit()
    db.refresh(user)
    return user    



## delete_user
@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    db.delete(user)
    db.commit()    




# we dont hide this from docs since its json route
## get_posts
@app.get("/api/posts", response_model=list[PostResponse])
def get_posts(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
    return posts




## Create Post   
## create_post
@app.post(
    "/api/posts",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_post(post: PostCreate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == post.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    new_post = models.Post(
        title=post.title,
        content=post.content,
        user_id=post.user_id,
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post




## get_post
@app.get("/api/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")



## get_post
@app.put("/api/posts/{post_id}", response_model=PostResponse)
def update_post_full(post_id: int,post_data:PostCreate ,db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()

    
    if not post:
       
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if post_data.user_id != post.user_id:

        result = db.execute(select(models.User).where(models.User.id==post_data.user_id),)
        user = result.scalars().first()

        if not user:
            raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    post.title  = post_data.title
    post.content  = post_data.content
    post.user_id  = post_data.user_id


    db.commit()
    db.refresh(post)
    return post


# patch update only updates fields sent by user
# dont update missing fields to none

@app.patch("/api/posts/{post_id}", response_model=PostResponse)
def update_post_partial(post_id: int,post_data:PostUpdate ,db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()

    
    if not post:
 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


    update_data = post_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(post, field, value)



    db.commit()
    db.refresh(post)
    return post


    ## get_post
@app.delete("/api/posts/{post_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
    
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    db.delete()
    db.commit()

    



## StarletteHTTPException Handler
@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."

    )

    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exception.status_code,
            content={"detail": message},
        )
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,
    )


