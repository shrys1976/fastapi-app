from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app =  FastAPI()



posts: list[dict] = [
    {
        "id": 1,
        "author": "user1",
        "title": "some title",
        "content": "some content.",
        "date_posted": "April 20, 2025",
    },
    {
        "id": 2,
        "author": "user2",
        "title": "second title",
        "content": "second content.",
        "date_posted": "April 21, 2025",
    },
]



@app.get("/posts",response_class = HTMLResponse,include_in_schema=False) # include in schema disables route visibility in fastapidocs
@app.get("/",response_class = HTMLResponse,include_in_schema=False)# response class changed to html since originally its json
def home():
    return f"<h1>{posts[0]['title']}</h1>" # now we can write html since response is changed

# we dont hide this from docs since its json route
@app.get("/api/posts")
def get_posts():
    return posts
