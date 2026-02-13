from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


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



@app.get("/posts", include_in_schema=False,name = "posts")  # include in schema disables route visibility in fastapidocs
@app.get("/", include_in_schema=False,name  = "home")  # response class changed to HTML since originally it's JSON
def home(request: Request) -> HTMLResponse:
    context = {
        "request": request,
        "posts": posts,
        "title": "Home",
    }
    return templates.TemplateResponse("home.html", context)

# we dont hide this from docs since its json route
@app.get("/api/posts")
def get_posts():
    return posts
