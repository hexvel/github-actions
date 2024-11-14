import hashlib
import hmac
import os
import subprocess

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

SECRET_TOKEN = "свой секретный ключ"
GIT_USERNAME = "юзернейм в гитхабе"
GIT_TOKEN = "персональный токен"

app = FastAPI()


async def verify_signature(request: Request):
    signature = request.headers.get("X-Hub-Signature-256")
    if signature is None:
        raise HTTPException(status_code=400, detail="Signature missing")

    body = await request.body()

    computed_signature = (
        "sha256=" + hmac.new(SECRET_TOKEN.encode(), body, hashlib.sha256).hexdigest()
    )

    if not hmac.compare_digest(computed_signature, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")


@app.post("/webhook")
async def github_webhook(request: Request):
    try:
        await verify_signature(request)
        data = await request.json()

        if data and data["ref"] == "refs/heads/main":
            os.chdir("/home/ubuntu/new_hex")

            git_url = f"https://{GIT_USERNAME}:{GIT_TOKEN}@github.com/hexvel/repo.git"
            subprocess.run(["git", "pull", git_url])

            subprocess.run(["sudo", "systemctl", "restart", "bot.service"])

        return JSONResponse(content={"message": "Received"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
