#!/usr/bin/env python3
"""Upload a video to YouTube (private by default).

First run: `yt-upload --auth` to log in. On a headless box, tunnel the port
from the machine with the browser: ssh -L 8765:localhost:8765 <this-host>

Without a saved token file, the contents of token.json can be supplied in the
YT_TOKEN environment variable instead (e.g. in a cloud environment).
"""
import argparse
import json
import os
import pathlib
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

CFG = pathlib.Path.home() / ".config/youtube-upload"
TOKEN = CFG / "token.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
PORT = 8765


def login():
    flow = InstalledAppFlow.from_client_secrets_file(CFG / "client_secret.json", SCOPES)
    return flow.run_local_server(port=PORT, open_browser=False)


def creds(interactive):
    from_env = not TOKEN.exists() and "YT_TOKEN" in os.environ
    if TOKEN.exists():
        c = Credentials.from_authorized_user_file(TOKEN, SCOPES)
    elif from_env:
        c = Credentials.from_authorized_user_info(json.loads(os.environ["YT_TOKEN"]), SCOPES)
    else:
        c = None
    if c and c.expired and c.refresh_token:
        try:
            c.refresh(Request())
        except Exception:
            c = None
    if not c or not c.valid:
        if not interactive:
            sys.exit("yt-upload: not logged in (or token expired). Run `yt-upload --auth` in a terminal.")
        c = login()
        from_env = False
    if not from_env:
        CFG.mkdir(parents=True, exist_ok=True)
        TOKEN.write_text(c.to_json())
        TOKEN.chmod(0o600)
    return c


def main():
    p = argparse.ArgumentParser()
    p.add_argument("file", nargs="?")
    p.add_argument("--auth", action="store_true", help="log in and save token, then exit")
    p.add_argument("--title")
    p.add_argument("--description", default="")
    p.add_argument("--tags", default="", help="comma-separated")
    p.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"])
    a = p.parse_args()

    if a.auth:
        creds(interactive=True)
        print(f"Logged in; token saved to {TOKEN}")
        return
    if not a.file or not a.title:
        p.error("file and --title are required")

    yt = build("youtube", "v3", credentials=creds(interactive=False))
    req = yt.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": a.title,
                "description": a.description,
                "tags": [t.strip() for t in a.tags.split(",") if t.strip()],
            },
            "status": {"privacyStatus": a.privacy, "selfDeclaredMadeForKids": False},
        },
        media_body=MediaFileUpload(a.file, chunksize=-1, resumable=True),
    )
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"{int(status.progress() * 100)}%", file=sys.stderr)
    print(f"https://youtu.be/{resp['id']}")


if __name__ == "__main__":
    main()
