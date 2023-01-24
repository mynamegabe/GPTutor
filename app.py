import uvicorn
from fastapi import (
    FastAPI,
    Request,
    Response,
    status,
    UploadFile,
    Form,
    File,
    WebSocket,
    HTTPException,
    BackgroundTasks,
    UploadFile,
)
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
import starlette.status as status
import sqlite3
import hashlib
import gpt
import requests
import urllib.parse
import random
import string
import json
import datetime
import os
import pytesseract
import base64
from typing import List, Optional
from PIL import Image
import io
import ast
import re
from unidecode import unidecode

middleware = [Middleware(SessionMiddleware, secret_key="sd78yf7s8adg789oasduioasdfh")]

app = FastAPI(middleware=middleware)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


conn = sqlite3.connect("hnr.db", check_same_thread=False)
# This is so that the .execute() results are stored in a dict and not a tuple
conn.row_factory = sqlite3.Row
with open("schema.sql") as fp:
    cur = conn.cursor()
    cur.executescript(fp.read())
    if 0 == 1:
        print("[=== START OF DB DATA DUMP ===]")
        rows = cur.execute("SELECT * FROM users")
        rows = rows.fetchall()
        print("users", len(rows))
        rows = cur.execute("SELECT * FROM materials")
        rows = rows.fetchall()
        print("materials", len(rows))
        rows = cur.execute("SELECT * FROM quizAttempts")
        rows = rows.fetchall()
        print("quizAttempts", len(rows))
        print("[=== END OF DB DATA DUMP ===]")
    cur.close()


@app.get("/")
def index(request: Request):
    # if request.session['user'] != None:
    #     return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login")
def login(request: Request):
    if (
        "user" in request.session
        and request.session["user"] != None
        and request.session["user"] != ""
    ):
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login(request: Request, email=Form(), password=Form()):
    password_hash = hashlib.sha256(
        password.encode()
    ).hexdigest()  # such secure, much wow
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT * FROM users WHERE email = ? AND password_hash = ?",
        (
            email,
            password_hash,
        ),
    )
    row = rows.fetchone()
    cur.close()
    if row is None:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid login. Please try again."},
        )
    request.session["user"] = row["id"]  # Cache session details
    request.session["email"] = row["email"]
    request.session["first_name"] = row["first_name"]
    request.session["last_name"] = row["last_name"]
    request.session["gpt_session_token"] = row["gpt_session_token"]
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)


@app.get("/register")
def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register")
def register(
    email=Form(), first_name=Form(), last_name=Form(), password=Form()
):  # TODO: Input sanitization
    print("register", email, first_name, last_name, password)
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = rows.fetchone()
    cur.close()
    if row is not None:
        return "Account with this email already exists"

    password_hash = hashlib.sha256(
        password.encode()
    ).hexdigest()  # such secure, much wow
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (email, first_name, last_name, password_hash) VALUES (?, ?, ?, ?)",
        (
            email,
            first_name,
            last_name,
            password_hash,
        ),
    )
    cur.close()
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


@app.get("/dashboard")
def dashboard(request: Request):
    if "user" not in request.session or request.session["user"] is None:
        return RedirectResponse(url="/login")
    user = request.session["user"]
    cur = conn.cursor()
    materials = cur.execute(
        "SELECT uuid, name, created, status FROM materials WHERE uid = ?", (user,)
    )
    materials = materials.fetchall()
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "user": user, "materials": materials}
    )


@app.get("/create")
def create(request: Request, url: Optional[str] = None):
    if "user" not in request.session:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("create.html", {"request": request, "url": url})


@app.get("/materials")
def materials(request: Request):
    if "user" not in request.session:
        return RedirectResponse(url="/login")
    cur = conn.cursor()
    materials = cur.execute(
        "SELECT * FROM materials WHERE uid = ?", (request.session["user"],)
    )
    materials = materials.fetchall()
    return templates.TemplateResponse(
        "materials.html", {"request": request, "materials": materials}
    )


@app.get("/contact")
def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})


@app.get("/logout")
def logout(request: Request):
    request.session["user"] = None
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie(key="session")  # I don't think this works lmfao
    return response


@app.get("/dumpurl")
def dumpurl(request: Request, url: str):
    response = requests.get(url).content
    response = urllib.parse.unquote(response)
    parsed_uri = urllib.parse.urlparse(url)
    hosturl = "{uri.scheme}://{uri.netloc}/".format(uri=parsed_uri)
    response = response.replace('href="/', f'href="{hosturl}/')
    response = response.replace('src="/', f'src="{hosturl}/')
    # response = urllib.parse.quote(response)
    return response


@app.post("/start")
async def start(
    request: Request,
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    query: Optional[str] = Form(None),
    selected: Optional[str] = Form(None),
    keyPoints: bool = Form(),
    openended: bool = Form(),
    mcq: bool = Form(),
    summary: bool = Form(),
    qtype: str = Form(),
    topic: str = Form(),
):
    if "user" not in request.session or request.session["user"] == None:
        return HTTPException(status_code=401, detail="Not logged in")
    uid = request.session["user"]
    gpt_session_token = request.session["gpt_session_token"]
    uuid = generateString(32)
    if file:
        if file.filename:
            file = await file.read()
            selected = OCR(io.BytesIO(file))
            print("Text = " + selected)
            qtype = "file"
    dev_status = "Processing"
    t = datetime.datetime.now()
    date = t.strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO materials (uid, name, uuid, query, selected, keyPoints, quiz, mcq, summary, status, created) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            uid,
            topic,
            uuid,
            query,
            selected,
            keyPoints,
            openended,
            mcq,
            summary,
            dev_status,
            date,
        ),
    )
    cur.close()
    q = query if qtype == "query" else selected
    q = selected if qtype == "file" else q

    if qtype == "query":
        response = requests.get(query)
        if response.status_code == 200:
            q = response.content.decode("utf-8")
            q = re.sub("<[^<]+?>", "", q)
            if len(q) > 1500:
                return "Query too long. Please try again with a shorter query."
        else:
            return "Invalid URL"
    background_tasks.add_task(
        generateItems, gpt_session_token, q, uuid, keyPoints, openended, mcq, summary
    )
    return RedirectResponse(url=f"/dashboard", status_code=status.HTTP_302_FOUND)


@app.get("/about")
def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


@app.get("/profile")
def profile(request: Request):
    uid = request.session["user"]  # Get session details
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM users WHERE id = ?", (uid,))
    row = rows.fetchone()
    cur.close()
    if row is None:
        return "An error occured. Please contact system admin."
    ## Get User Info
    email = row["email"]
    first_name = row["first_name"]
    last_name = row["last_name"]
    gpt_session_token = row["gpt_session_token"]

    ## Send to the page
    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "gpt_session_token": gpt_session_token,
        },
    )


@app.post("/profile")
def profile(
    request: Request,
    email=Form(),
    first_name=Form(),
    last_name=Form(),
    gpt_session_token=Form(),
):  # TODO: Input sanitization
    print("Update Profile", email, first_name, last_name, gpt_session_token)
    user = request.session["user"]
    ## Update DB
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET email = ?, first_name = ?, last_name = ?, gpt_session_token = ? WHERE id = ?",
        (
            email,
            first_name,
            last_name,
            gpt_session_token,
            user,
        ),
    )
    conn.commit()
    cur.close()
    ## Update Cookies
    request.session["email"] = email
    request.session["first_name"] = first_name
    request.session["last_name"] = last_name
    request.session["gpt_session_token"] = gpt_session_token
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)


@app.get("/materials/{uuid}")
def materials(request: Request, uuid: str):
    # if "user" not in request.session:
    #     return RedirectResponse(url="/login")
    cur = conn.cursor()
    uid = request.session["user"] if ("user" in request.session) else ""
    materials = cur.execute(
        "SELECT uuid, name, privacy, openendedArray, mcqArray, summaryResult, keyPointsArray FROM materials WHERE uuid = ? AND uid = ? OR uuid = ? AND privacy = 'public'",
        (uuid, uid, uuid),
    )
    materials = materials.fetchone()
    cur.close()
    materials = {
        "openended": json.loads(materials["openendedArray"]),
        "mcq": json.loads(materials["mcqArray"]),
        "summary": materials["summaryResult"],
        "keyPoints": json.loads(materials["keyPointsArray"]),
        "name": materials["name"],
        "uuid": materials["uuid"],
        "privacy": materials["privacy"],
    }
    print(materials)
    return templates.TemplateResponse(
        "material.html", {"request": request, "materials": materials}
    )


@app.get("/materialsedit/{uuid}")
def materialsEdit(request: Request, uuid: str):
    uid = request.session["user"]  # Get session details
    cur = conn.cursor()
    materials = cur.execute(
        "SELECT name, openendedArray, mcqArray, summaryResult, keyPointsArray FROM materials WHERE uuid = ? AND uid = ?",
        (uuid, uid),
    )
    materials = materials.fetchone()
    cur.close()
    return templates.TemplateResponse(
        "material_edit.html",
        {
            "request": request,
            "uuid": uuid,
            "materials_mcq": materials["mcqArray"],
            "materials_oed": materials["openendedArray"],
            "materials_sud": materials["summaryResult"],
            "materials_kpd": materials["keyPointsArray"],
            "materials_name": materials["name"],
        },
    )


@app.post("/materialsedit/{uuid}")
def materialsEdit(
    request: Request,
    uuid: str,
    materials_name=Form(None),
    materials_mcq: Optional[str] = Form(None),
    materials_oed: Optional[str] = Form(None),
    materials_kpd: Optional[str] = Form(None),
    materials_sud: Optional[str] = Form(None),
):  # TODO: Input sanitization
    uid = request.session["user"]  # Get session details
    cur = conn.cursor()
    cur.execute(
        "UPDATE materials SET name = ?, openendedArray = ?, mcqArray = ?, summaryResult = ?, keyPointsArray = ? WHERE uuid = ? AND uid = ?",
        (
            materials_name,
            materials_oed,
            materials_mcq,
            materials_sud,
            materials_kpd,
            uuid,
            uid,
        ),
    )
    conn.commit()
    cur.close()
    return RedirectResponse(url=f"/materials/{uuid}", status_code=status.HTTP_302_FOUND)


@app.get("/materials/{uuid}/delete")
def materialsDelete(request: Request, uuid: str):
    uid = request.session["user"]  # Get session details
    cur = conn.cursor()
    materials = cur.execute(
        "DELETE FROM materials WHERE uuid = ? AND uid = ?", (uuid, uid)
    )
    materials = materials.fetchone()
    conn.commit()
    cur.close()
    return RedirectResponse(url=f"/materials", status_code=status.HTTP_302_FOUND)
    # return templates.TemplateResponse("material_delete.html", {"request": request, "name": name})


@app.get("/materials/{uuid}/quizlet")
def materials(request: Request, uuid: str, background_tasks: BackgroundTasks):
    if "user" not in request.session:
        return RedirectResponse(url="/login")
    materials = generateMaterials(uuid, request.session["user"])
    export = quizletExport(materials)
    tmpfile = "tmp_" + generateString(32)
    with open(tmpfile, "w") as f:
        f.write(export[0] + "\n\nDelimiter: " + export[1])
    background_tasks.add_task(os.remove, tmpfile)
    return FileResponse(
        tmpfile, media_type="text/plain", filename=materials["name"] + ".txt"
    )


@app.get("/materials/{uuid}/quiz")
def quiz(request: Request, uuid: str):
    materials = generateMaterials(uuid, request.session["user"])
    questions = []
    for v in materials["openended"]:
        questions.append(v[0].strip())
    return templates.TemplateResponse(
        "quiz.html",
        {
            "request": request,
            "questions": questions,
            "materials": {"name": materials["name"], "uuid": uuid},
        },
    )


@app.post("/materials/{uuid}/quiz")
async def quiz(request: Request, uuid: str):
    attemptAnswers = await request.json()
    attemptAnswers = attemptAnswers["answers"]
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO quizAttempts (uid, uuid, answers) VALUES (?, ?, ?)",
        (request.session["user"], uuid, json.dumps(attemptAnswers)),
    )
    conn.commit()
    attemptId = cur.lastrowid
    cur.close()
    return JSONResponse({"attemptId": attemptId})


@app.get("/materials/{uuid}/quiz/attempt/{attemptId}")
def quiz(request: Request, uuid: str, attemptId: int):
    cur = conn.cursor()
    attemptAnswers = cur.execute(
        "SELECT answers FROM quizAttempts WHERE id = ?", (attemptId,)
    ).fetchone()["answers"]
    attemptAnswers = json.loads(attemptAnswers)
    materials = generateMaterials(uuid, request.session["user"])
    qna = []
    for i in range(len(materials["openended"])):
        o = materials["openended"][i]
        o.append(attemptAnswers[i])
        qna.append(o)
    return templates.TemplateResponse(
        "quizResults.html",
        {
            "request": request,
            "questions": qna,
            "materials": {"name": materials["name"]},
        },
    )


@app.get("/materials/{uuid}/mcq")
def quiz(request: Request, uuid: str):
    materials = generateMaterials(uuid, request.session["user"])
    questions = []
    choices = []
    for v in materials["mcq"]:
        questions.append(v[0].strip())
        choices.append(v[1])
    return templates.TemplateResponse(
        "mcq.html",
        {
            "request": request,
            "questions": questions,
            "choices": choices,
            "materials": {"name": materials["name"], "uuid": uuid},
        },
    )


@app.post("/materials/{uuid}/mcq")
async def quiz(request: Request, uuid: str):
    attemptAnswers = await request.json()
    attemptAnswers = attemptAnswers["answers"]
    materials = generateMaterials(uuid, request.session["user"])
    if len(attemptAnswers) < len(
        materials["mcq"]
    ):  # TODO: Prevent "Internal Server Error"
        return "Not all questions have been answered"
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO quizAttempts (uid, uuid, answers) VALUES (?, ?, ?)",
        (request.session["user"], uuid, json.dumps(attemptAnswers)),
    )
    conn.commit()
    attemptId = cur.lastrowid
    cur.close()
    return JSONResponse({"attemptId": attemptId})


@app.get("/materials/{uuid}/mcq/attempt/{attemptId}")
def quiz(request: Request, uuid: str, attemptId: int):
    cur = conn.cursor()
    attemptAnswers = cur.execute(
        "SELECT answers FROM quizAttempts WHERE id = ?", (attemptId,)
    ).fetchone()["answers"]
    attemptAnswers = json.loads(attemptAnswers)
    materials = generateMaterials(uuid, request.session["user"])
    qna = []
    for i in range(len(materials["mcq"])):
        o = [
            materials["mcq"][i][0],
            materials["mcq"][i][2]
            + " - "
            + materials["mcq"][i][1][ord(materials["mcq"][i][2]) - 65],
        ]  # very cursed
        o.append(
            attemptAnswers[i]
            + " - "
            + materials["mcq"][i][1][ord(attemptAnswers[i]) - 65]
        )  # very cursed
        qna.append(o)
    return templates.TemplateResponse(
        "mcqResults.html",
        {
            "request": request,
            "questions": qna,
            "materials": {"name": materials["name"]},
        },
    )


@app.post("/materials/{uuid}/privacy")
def privacy(request: Request, uuid: str, privacy=str):
    if "user" not in request.session:
        return RedirectResponse(url="/login")
    assert privacy in ["public", "private"]
    uid = request.session["user"]
    cur = conn.cursor()
    cur.execute(
        "UPDATE materials SET privacy = ? WHERE uuid = ? AND uid = ?",
        (
            privacy,
            uuid,
            uid,
        ),
    )
    conn.commit()
    cur.close()
    return JSONResponse({"privacy": privacy})


@app.get("/materials/{uuid}/tts/{material}")
def tts(request: Request, uuid: str, material: str):
    materials = generateMaterials(uuid, request.session["user"])
    print(materials)
    if material == "summary":
        b64tts = textToSpeech(materials["summary"])
    elif material == "keyPoints":
        b64tts = textToSpeech(materials["keyPoints"])
    elif material == "openended":
        b64tts = textToSpeech(materials["openended"])
    elif material == "mcq":
        b64tts = textToSpeech(materials["mcq"])
    else:
        return "Invalid material"
    return JSONResponse({"material": material, "uuid": uuid, "tts": b64tts.decode()})


def generateMaterials(uuid: str, uid: str):
    cur = conn.cursor()
    materials = cur.execute(
        "SELECT name, openendedArray, mcqArray, summaryResult, keyPointsArray FROM materials WHERE uuid = ? AND uid = ? OR uuid = ? AND privacy = 'public'",
        (
            uuid,
            uid,
            uuid,
        ),
    )
    materials = materials.fetchone()
    cur.close()
    return {
        "openended": json.loads(materials["openendedArray"]),
        "mcq": json.loads(materials["mcqArray"]),
        "summary": materials["summaryResult"],
        "keyPoints": json.loads(materials["keyPointsArray"]),
        "name": materials["name"],
    }


def quizletExport(raw_materials):
    materials = []
    for v in raw_materials["openended"]:  # Strip all whitespaces
        materials.append([v[0].strip(), v[1].strip()])

    while True:
        delim = "<" + generateString(4) + ">"
        valid = True
        for v in materials:  # Test if delim is suitable
            if (delim in v[0]) or (delim in v[1]):
                valid = False
                break
        if valid:
            break

    res = ""
    for v in materials:
        res += v[0] + delim + v[1] + "\n"
    return [res, delim]


def generateString(length):
    return "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(length)
    )


def generateItems(gpt_session_token, q, uuid, keyPoints, openended, mcq, summary):
    cur = conn.cursor()
    if openended:
        openendedArray = json.dumps(gpt.generateQuiz(gpt_session_token, q))
        cur.execute(
            "UPDATE materials SET openendedArray = ? WHERE uuid = ?",
            (
                openendedArray,
                uuid,
            ),
        )
    if mcq:
        mcqArray = json.dumps(gpt.generateMCQ(gpt_session_token, q))
        cur.execute(
            "UPDATE materials SET mcqArray = ? WHERE uuid = ?",
            (
                mcqArray,
                uuid,
            ),
        )
    if keyPoints:
        keyPointsArray = json.dumps(gpt.generateKeyPoints(gpt_session_token, q))
        cur.execute(
            "UPDATE materials SET keyPointsArray = ? WHERE uuid = ?",
            (
                keyPointsArray,
                uuid,
            ),
        )
    if summary:
        summaryResult = gpt.generateSummary(gpt_session_token, q)
        cur.execute(
            "UPDATE materials SET summaryResult = ? WHERE uuid = ?",
            (
                summaryResult,
                uuid,
            ),
        )

    cur.execute(
        "UPDATE materials SET status = ? WHERE uuid = ?",
        (
            "Completed",
            uuid,
        ),
    )
    conn.commit()
    cur.close()


def textToSpeech(txt):
    # txt = unidecode(txt)
    url = "https://voicerss-text-to-speech.p.rapidapi.com/"
    querystring = {"key": "47b59a4b2a884401863afa90068d1374"}
    payload = f"src={txt}&hl=en-us&r=1&c=mp3&f=8khz_8bit_mono"
    headers = {
        "content-type": "application/x-www-form-urlencoded",
        "X-RapidAPI-Key": "ba90367678msh5b0f44dc29ca365p1fcda3jsn488cd6f9278d",
        "X-RapidAPI-Host": "voicerss-text-to-speech.p.rapidapi.com",
    }
    response = requests.request(
        "POST", url, data=payload, headers=headers, params=querystring
    )
    response = base64.b64encode(response.content)
    return response


def OCR(image):
    # If you don't have tesseract executable in your PATH, include the following:
    # pytesseract.pytesseract.tesseract_cmd = 'C:/Users/joshu/AppData/Local/Programs/Tesseract-OCR' ## Change based on your user!

    # Simple image to string
    img = Image.open(image)
    return pytesseract.image_to_string(img)


@app.exception_handler(404)
async def custom_404_handler(_, __):
    return templates.TemplateResponse("404.html", {"request": _})


@app.exception_handler(500)
async def custom_404_handler(_, __):
    return templates.TemplateResponse("500.html", {"request": _})


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
