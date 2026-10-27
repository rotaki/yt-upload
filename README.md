# yt-upload

Personal command-line tool that uploads videos to my own YouTube channel
(private by default) via the YouTube Data API.

```bash
pip install -r requirements.txt
./yt_upload.py --auth                 # one-time login
./yt_upload.py video.mp4 --title "My video" [--description ...] [--tags a,b] [--privacy private|unlisted|public]
```

Credentials live in `~/.config/youtube-upload/` (`client_secret.json`, `token.json`).
In environments without that directory, put the contents of `token.json` in the
`YT_TOKEN` environment variable.
