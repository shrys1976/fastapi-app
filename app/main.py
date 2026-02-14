from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from schemas import PostCreate, PostResponse

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
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


@app.get("/posts", include_in_schema=False, name="posts")
@app.get("/", include_in_schema=False, name="home")
def home(request: Request) -> HTMLResponse:
    context = {
        "request": request,
        "posts": posts,
        "title": "Home",
    }
    return templates.TemplateResponse("home.html", context)


@app.get("/posts/{post_id}", include_in_schema=False)
def post_page(post_id: int, request: Request) -> HTMLResponse:
    for post in posts:
        if post.get("id") == post_id:
            title = post["title"][:50]
            context = {
                "request": request,
                "post": post,
                "title": title,
            }
            return templates.TemplateResponse("post.html", context)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


# we dont hide this from docs since its json route
@app.get("/api/posts", response_model=list[PostResponse])
def get_posts():
    return posts



## Create Post
@app.post(
    "/api/posts",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_post(post: PostCreate):
    new_id = max(p["id"] for p in posts) + 1 if posts else 1
    new_post = {
        "id": new_id,
        "author": post.author,
        "title": post.title,
        "content": post.content,
        "date_posted": "April 23, 2025",
    }
    posts.append(new_post)
    return new_post




@app.get("/api/posts/{post_id}", response_model=PostResponse) # not a list since we are returning a single post
def get_post(post_id: int):
    for post in posts:
        if post.get("id") == post_id:
            return post

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)



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


