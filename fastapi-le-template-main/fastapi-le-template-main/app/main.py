import uvicorn
from fastapi import FastAPI, Request, status, Form
from fastapi.responses import RedirectResponse
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from app.config import get_settings
from app.dependencies import IsUserLoggedIn, SessionDep, AuthDep
from fastapi.templating import Jinja2Templates
from app.utilities import get_flashed_messages
from jinja2 import Environment, FileSystemLoader
from sqlmodel import select
from app.models import User, Album, Track, Comment, Reaction
from app.utilities import flash, create_access_token
from fastapi.staticfiles import StaticFiles


app = FastAPI(middleware=[
    Middleware(SessionMiddleware, secret_key=get_settings().secret_key)
]
)
template_env = Environment(loader = FileSystemLoader("app/templates",), )
template_env.globals['get_flashed_messages'] = get_flashed_messages
templates = Jinja2Templates(env=template_env)
static_files = StaticFiles(directory="app/static")

app.mount("/static", static_files, name="static")


@app.get('/', response_class=RedirectResponse)
async def index_view(
  request: Request,
  user_logged_in: IsUserLoggedIn,
):
  if user_logged_in:
    return RedirectResponse(url=request.url_for('home_view'), status_code=status.HTTP_303_SEE_OTHER)
  return RedirectResponse(url=request.url_for('login_view'), status_code=status.HTTP_303_SEE_OTHER)

@app.get("/login")
async def login_view(
  user_logged_in: IsUserLoggedIn,
  request: Request,
):
  if user_logged_in:
    return RedirectResponse(url=request.url_for('home_view'), status_code=status.HTTP_303_SEE_OTHER)
  return templates.TemplateResponse(
          request=request, 
          name="login.html",
      )

@app.post('/login')
def login_action(
  request: Request,
  db: SessionDep,
  username: str = Form(),
  password: str = Form(),
):
  
  user = db.exec(select(User).where(User.username == username)).one_or_none()
  if user and user.check_password(password):
    response = RedirectResponse(url=request.url_for("index_view"), status_code=status.HTTP_303_SEE_OTHER)
    access_token = create_access_token(data={"sub": f"{user.id}"})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=False,
        samesite="lax",
        secure=True,
    )    
    return response
  else:
    flash(request, 'Invalid username or password')
    return RedirectResponse(url=request.url_for('login_view'), status_code=status.HTTP_303_SEE_OTHER)


@app.get('/app')
def home_view(request: Request, user: AuthDep, db: SessionDep):
  # View Albums - fetch all albums
  albums = db.exec(select(Album)).all()
  
  # Get selected album and tracks from session
  selected_album_id = request.session.get('selected_album_id')
  selected_track_id = request.session.get('selected_track_id')
  tracks = []
  comments = []
  
  if selected_album_id:
    tracks = db.exec(select(Track).where(Track.album_id == selected_album_id)).all()
  
  if selected_track_id:
    comments = db.exec(select(Comment).where(Comment.track_id == selected_track_id)).all()
  
  return templates.TemplateResponse(
          request=request, 
          name="index.html",
          context={
            "albums": albums,
            "selected_album_id": selected_album_id,
            "tracks": tracks,
            "selected_track_id": selected_track_id,
            "comments": comments,
          }
      )

@app.post('/albums/{album_id}/select')
def select_album(album_id: int, request: Request, user: AuthDep):
  # View Album Tracks - select an album
  request.session['selected_album_id'] = album_id
  request.session['selected_track_id'] = None  # Reset track selection
  return RedirectResponse(url=request.url_for('home_view'), status_code=status.HTTP_303_SEE_OTHER)

@app.post('/tracks/{track_id}/select')
def select_track(track_id: int, request: Request, user: AuthDep):
  # View Track Comments - select a track
  request.session['selected_track_id'] = track_id
  return RedirectResponse(url=request.url_for('home_view'), status_code=status.HTTP_303_SEE_OTHER)

@app.post('/comments')
def add_comment(
  request: Request,
  user: AuthDep,
  db: SessionDep,
  track_id: int = Form(),
  text: str = Form(),
):
  # Comment on Track - add a comment
  comment = Comment(track_id=track_id, user_id=user.id, text=text)
  db.add(comment)
  db.commit()
  db.refresh(comment)
  request.session['selected_track_id'] = track_id
  return RedirectResponse(url=request.url_for('home_view'), status_code=status.HTTP_303_SEE_OTHER)

@app.post('/reactions')
def add_reaction(
  request: Request,
  user: AuthDep,
  db: SessionDep,
  track_id: int = Form(),
  reaction_type: str = Form(),
):
  # React to Track - add like/dislike
  reaction = Reaction(track_id=track_id, user_id=user.id, reaction_type=reaction_type)
  db.add(reaction)
  db.commit()
  db.refresh(reaction)
  request.session['selected_track_id'] = track_id
  return RedirectResponse(url=request.url_for('home_view'), status_code=status.HTTP_303_SEE_OTHER)

@app.post('/comments/{comment_id}/delete')
def delete_comment(
  comment_id: int,
  request: Request,
  user: AuthDep,
  db: SessionDep,
):
  # Delete Comment - delete a comment user made
  comment = db.exec(select(Comment).where(Comment.id == comment_id)).one_or_none()
  if comment and comment.user_id == user.id:
    track_id = comment.track_id
    db.delete(comment)
    db.commit()
    request.session['selected_track_id'] = track_id
  return RedirectResponse(url=request.url_for('home_view'), status_code=status.HTTP_303_SEE_OTHER)

@app.get('/logout')
async def logout(request: Request):
  response = RedirectResponse(url=request.url_for("login_view"), status_code=status.HTTP_303_SEE_OTHER)
  response.delete_cookie(
      key="access_token", 
      httponly=True,
      samesite="none",
      secure=True
  )
  flash(request, 'logged out')
  return response