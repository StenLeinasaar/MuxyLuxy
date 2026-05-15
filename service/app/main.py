from fastapi import FastAPI

app = FastAPI(title="Ansible Roller")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
