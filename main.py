from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
import yt_dlp
import os
import uuid
import subprocess

app = FastAPI()

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_youtube(url: str) -> str:
    video_id = str(uuid.uuid4())
    filepath = f"{OUTPUT_DIR}/{video_id}.mp4"
    ydl_opts = {
        "outtmpl": filepath,
        "format": "bestvideo+bestaudio/best"
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return filepath

def convert_9_16(input_path: str) -> str:
    output_path = input_path.replace(".mp4", "_reel.mp4")
    command = [
        "ffmpeg", "-i", input_path,
        "-vf", "crop=in_h*9/16:in_h:(in_w-out_w)/2:0",
        "-preset", "fast",
        output_path
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return output_path

@app.post("/process_url")
def process_url(video_url: str = Form(...)):
    try:
        downloaded = download_youtube(video_url)
        result = convert_9_16(downloaded)
        return {"status": "success", "download_url": f"/get_video/{os.path.basename(result)}"}
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.get("/get_video/{filename}")
def get_video(filename: str):
    filepath = f"{OUTPUT_DIR}/{filename}"
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="video/mp4")
    return JSONResponse({"error": "File not found"}, status_code=404)
