from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app =  FastAPI()

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



@app.get("/posts",include_in_schema=False) # include in schema disables route visibility in fastapidocs
@app.get("/",include_in_schema=False)# response class changed to html since originally its json
def home(request:Request):
    return templates.TemplateResponse(request,"home.html",{"posts":posts}) # now we can write html since response is changed

# we dont hide this from docs since its json route
@app.get("/api/posts")
def get_posts():
    return posts
