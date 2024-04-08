from fastapi import FastAPI, HTTPException, Request, Depends
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FollowEvent
from linebot.exceptions import InvalidSignatureError
from linebot import LineBotApi, WebhookHandler
from starlette.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import uvicorn
import os
import json
from pydantic import BaseModel
import sqlite3


class User(BaseModel):
    lineId: str
    googleEmail: str
    name: str
    phone: str


class Database:
    def __init__(self):
        self.conn = sqlite3.connect('database.db')
        self.cursor = self.conn.cursor()

    def close(self):
        self.conn.close()

    def insert_user(self, user: User):
        self.cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)",
                            (user.lineId, user.googleEmail, user.name, user.phone))
        self.conn.commit()


class YouTubeAuth:
    def __init__(self):
        self.client_info = self.get_client_info()
        self.CLIENT_ID = self.client_info['client_id']
        self.CLIENT_SECRET = self.client_info['client_secret']
        self.REDIRECT_URI = self.client_info['redirect_uris'][0]
        self.AUTH_URI = self.client_info['auth_uri']
        self.TOKEN_URI = self.client_info['token_uri']
        self.SCOPES = [
            "https://www.googleapis.com/auth/youtube.force-ssl",
            "https://www.googleapis.com/auth/youtube.channel-memberships.creator"
        ]

    def get_client_info(self):
        with open('client_secret.json', 'r') as f:
            data = json.load(f)
        return data['web']

    def authenticate_user(self):
        flow = Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": self.CLIENT_ID,
                    "client_secret": self.CLIENT_SECRET,
                    "auth_uri": self.AUTH_URI,
                    "token_uri": self.TOKEN_URI,
                    "redirect_uris": [self.REDIRECT_URI],
                }
            },
            scopes=self.SCOPES,
        )
        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            state="random_state_string",
        )
        return RedirectResponse(authorization_url)

    def callback(self, code: str, state: str):
        flow = Flow.from_client_config(
            client_config={
                "web": {
                    "client_id": self.CLIENT_ID,
                    "client_secret": self.CLIENT_SECRET,
                    "auth_uri": self.AUTH_URI,
                    "token_uri": self.TOKEN_URI,
                    "redirect_uri": self.REDIRECT_URI,
                }
            },
            scopes=self.SCOPES,
            state=state,
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials
        service = build("youtube", "v3", credentials=credentials)
        return {"message": "User authenticated successfully"}

    def is_member(self, token: str):
        service = build("youtube", "v3", credentials=token)
        try:
            request = service.members().list(part="snippet")
            response = request.execute()
            members = [item['snippet']['memberDetails']['displayName']
                       for item in response['items']]
            return {"is_member": bool(members)}
        except HttpError as e:
            return {"error": str(e)}


class LineBot:
    def __init__(self):
        self.line_bot_api = LineBotApi('YOUR_CHANNEL_ACCESS_TOKEN')
        self.handler = WebhookHandler('YOUR_CHANNEL_SECRET')

    async def callback(self, request: Request):
        signature = request.headers['X-Line-Signature']
        body = await request.body()
        body = body.decode('utf-8')
        try:
            self.handler.handle(body, signature)
        except InvalidSignatureError:
            raise HTTPException(status_code=400)
        return 'OK'

    def handle_follow(self, event):
        self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='Got follow event'))

    def handle_message(self, event):
        self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='Got message event'))


def main():
    youtube_auth = YouTubeAuth()
    line_bot = LineBot()

    app = FastAPI()

    @app.on_event("shutdown")
    def shutdown_event():
        db.close()

    @app.get("/auth")
    def auth(youtube_auth: YouTubeAuth = Depends(YouTubeAuth)):
        return youtube_auth.authenticate_user()

    @app.get("/youtube/callback")
    def callback(code: str, state: str, youtube_auth: YouTubeAuth = Depends(YouTubeAuth)):
        return youtube_auth.callback(code, state)

    @app.get("/is_member")
    def is_member(token: str, youtube_auth: YouTubeAuth = Depends(YouTubeAuth)):
        return youtube_auth.is_member(token)

    # @app.post("/linebot/callback")
    # async def callback(request: Request, line_bot: LineBot = Depends(LineBot)):
    #     return await line_bot.callback(request)

    # @app.post("/api/register")
    # async def register(user: User, db: Database = Depends(Database)):
    #     db.insert_user(user)
    #     return {"success": True}

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
