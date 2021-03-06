from fastapi import FastAPI, File, UploadFile, Response, Header
from fastapi.responses import FileResponse
from typing import Optional
from deta import Deta
from pydantic import BaseModel
import hashlib
import jwt
import uuid
import json
from datetime import datetime, timedelta
from fastapi import File, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# pydantic to declare body of put or post
app = FastAPI()
a = "c02ff9ee_aRR2Gi3m4xe76"
deta = Deta(a+"F8txNbk77WqghL4nKKs")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def validateToken(token):
    try:
        validation = jwt.decode(token, 'UnaiSimon', algorithms="HS256")
        return True
    except:
        return False


@app.get("/")
def read_root():
    return {"message": "Let's get Started"}

class User(BaseModel):
    fName: str
    lName: str
    username: str
    email: str
    password: str

@app.post("/api/signup")
def signup(user: User):
    
    userdb = deta.Base("Notecaster_User")
    
    #hash the password
    user.password = hashlib.sha256(user.password.encode()).hexdigest()
    
    createUser = {
        "fName": user.fName,
        "lName": user.lName,
        "username": user.username,
        "email": user.email,
        "password": user.password
    }
    
    try:
        newuser = userdb.insert(createUser, user.username)
    except:
        return({
            "status": 409,
            "message": "User already exists."
        })
        
    JWT_SECRET = 'UnaiSimon'
    JWT_ALGORITHM = 'HS256'
    JWT_EXP_DELTA_SECONDS = 2628000
    payload = {'exp': datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS)}        
    jwt_token = jwt.encode(payload, JWT_SECRET, JWT_ALGORITHM)
    
    return({
        "status": 201,
        "message": "User created successfully.",
        "token": jwt_token,
        "key": user.username,
        "fName": user.fName,
        "lName": user.lName,
        "username": user.username,
        "email": user.email,
    })
    
    
class Login(BaseModel):
    username: str
    password: str
    
@app.post("/api/login")
def loginUser(login: Login):
    username = login.username
    password = login.password
    hashedPassword = hashlib.sha256(login.password.encode()).hexdigest()
    userdb = deta.Base("Notecaster_User")
    
    #check if username exists
    theUser = next(userdb.fetch({"username": username}))
    if len(theUser) == 0:
        return({
            "status": 404,
            "message": "Username does not exist."
        })
        
    theUser = theUser[0]
    
    #check password
    if theUser['password'] != hashedPassword:
        return({
            "status": 403,
            "message": "Password does not match."
        })
        
    #generate token
    JWT_SECRET = 'UnaiSimon'
    JWT_ALGORITHM = 'HS256'
    JWT_EXP_DELTA_SECONDS = 2628000
    payload = {'exp': datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA_SECONDS)}        
    jwt_token = jwt.encode(payload, JWT_SECRET, JWT_ALGORITHM)
    
    return({
        "status": 200,
        "message": "Successfully Logged In.",
        "token": jwt_token,
        "fName": theUser['fName'],
        "lName": theUser['lName'],
        "username": theUser['username'],
        "email": theUser['email'],
    })
        
class Subject(BaseModel):
    username: str
    name: str
    about: str

@app.post("/api/subjects")
def createproject(subject: Subject, Authorization: Optional[str] = Header(None)):
    
    if validateToken(Authorization) is False:
        return {
            "status": 401,
            "message": "Invalid Token"
        }
    
    name = subject.name
    about = subject.about
    username = subject.username
    
    subjectdb = deta.Base("Notecaster_Subject")
    
    createSubject = {
        "username": username,
        "name": name,
        "about": about
    }
    
    try:
        newSubject = subjectdb.insert(createSubject)
        return newSubject
    
    except:
        return({
            "status": 500,
            "message": "Some Error Occurred."
        })
        
@app.get("/api/subjects/{username}")
def getprojects(username: str, Authorization: Optional[str] = Header(None)):
    
    if validateToken(Authorization) is False:
        return {
            "status": 401,
            "message": "Invalid Token"
        }
    
    subjectdb = deta.Base("Notecaster_Subject")
    allSubjects = next(subjectdb.fetch({"username": username}))
    return allSubjects

@app.get("/api/subject/{key}")
def getproject(key: str, Authorization: Optional[str] = Header(None)):
    
    if validateToken(Authorization) is False:
        return {
            "status": 401,
            "message": "Invalid Token"
        }
    
    try:
        subjectdb = deta.Base("Notecaster_Subject")
        theSubject = subjectdb.get(key)
        return theSubject
    
    except:
        return({
            "status": 404,
            "message": "Project Does not Exist"
        })

@app.put("/api/subject/{key}")
def updateproject(key: str, subject: Subject, Authorization: Optional[str] = Header(None)):
    
    if validateToken(Authorization) is False:
        return {
            "status": 401,
            "message": "Invalid Token"
        }
    
    try:
        subjectdb = deta.Base("Notecaster_Subject")
        theSubject = subjectdb.get(key)
        theSubject['name'] = subject.name
        theSubject['about'] = subject.about
        theSubject = subjectdb.put(theSubject)
        return theSubject
    
    except:
        return({
            "status": 404,
            "message": "Project Does not Exist"
        })

@app.delete("/api/subject/{key}")
def getproject(key: str, Authorization: Optional[str] = Header(None)):
    
    if validateToken(Authorization) is False:
        return {
            "status": 401,
            "message": "Invalid Token"
        }
    
    try:
        subjectdb = deta.Base("Notecaster_Subject")
        subjectdb.delete(key)
        return ({
            "status": 203,
            "message": "Deleted Successfully."
        })
    
    except:
        return({
            "status": 404,
            "message": "Project Does not Exist"
        })

@app.put("/api/subjectimage/{key}")
def updateImage(key: str = "", file: UploadFile = File(...), Authorization: Optional[str] = Header(None)):
    
    if validateToken(Authorization) is False:
        return {
            "status": 401,
            "message": "Invalid Token"
        }
    
    subjectDrive = deta.Drive("Notecaster_Subject")
    
    fileName = str(uuid.uuid4())
    fileExtension = file.filename.split(".")[1]
    fileName += "."+fileExtension
    
    subjectDrive.put(name=fileName, data=file.file, content_type="image/"+fileExtension)

    #update image location in db
    subjectdb = deta.Base("Notecaster_Subject")
    theSubject = subjectdb.get(key)
    theSubject['image'] = fileName
    theSubject = subjectdb.put(theSubject)
    theSubject['status'] = 200
    return theSubject

@app.put("/api/removesubjectimage/{key}")
def deleteImage(key: str = "", file: UploadFile = File(...), Authorization: Optional[str] = Header(None)):
    
    if validateToken(Authorization) is False:
        return {
            "status": 401,
            "message": "Invalid Token"
        }
    
    subjectDrive = deta.Drive("Notecaster_Subject")
    subjectdb = deta.Base("Notecaster_Subject")
    theSubject = subjectdb.get(key)
    
    thatImage = theSubject['image']
    deleted_file = subjectDrive.delete(thatImage)
    
    del theSubject['image']
    
    theSubject = subjectdb.put(theSubject)
    return theSubject

@app.get("/api/getsubjectimage/{key}")
def getImage(key: str = "", Authorization: Optional[str] = Header(None)):
    
    if validateToken(Authorization) is False:
        return {
            "status": 401,
            "message": "Invalid Token"
        }
    
    subjectDrive = deta.Drive("Notecaster_Subject")
    subjectdb = deta.Base("Notecaster_Subject")
    theSubject = subjectdb.get(key)
    
    try:
        imageFile = subjectDrive.get(theSubject['image'])
        imageExtension = theSubject['image'].split(".")[1]
        return StreamingResponse(imageFile.iter_chunks(1024), media_type="image/"+imageExtension)
    except:
        return({
            "status": 404,
            "message": "Image Does not Exist"
        })
        
        
@app.post("/api/uploadimage")
def uploadImage(file: UploadFile = File(...), Authorization: Optional[str] = Header(None)):
    
    if validateToken(Authorization) is False:
        return {
            "status": 401,
            "message": "Invalid Token"
        }
    
    subjectDrive = deta.Drive("Notecaster_Image")
    
    fileName = str(uuid.uuid4())
    fileExtension = file.filename.split(".")[1]
    fileName += "."+fileExtension
    
    subjectDrive.put(name=fileName, data=file.file, content_type="image/"+fileExtension)
    
    return {
        "status": 200,
        "link": "https://notecaster-backend.deta.dev/getimage/"+fileName
    }
    
@app.get("/api/getimage/{imageLocation}")
def getImage(imageLocation: str, Authorization: Optional[str] = Header(None)):
    
    if validateToken(Authorization) is False:
        return {
            "status": 401,
            "message": "Invalid Token"
        }
    
    subjectDrive = deta.Drive("Notecaster_Image")
    try:
        imageFile = subjectDrive.get(imageLocation)
        imageExtension = imageLocation.split(".")[1]
        return StreamingResponse(imageFile.iter_chunks(1024), media_type="image/"+imageExtension)
    except:
        return({
            "status": 404,
            "message": "Image Does not Exist"
        })
        

#APIs for Notes

#create a note for project
class Note(BaseModel):
    name: str
    about: str
    subject: str
    username: str

@app.post("/api/notes")
def createproject(note: Note, Authorization: Optional[str] = Header(None)):
    
    if validateToken(Authorization) is False:
        return {
            "status": 401,
            "message": "Invalid Token"
        }
    
    notedb = deta.Base("Notecaster_Note")
    
    noter = {
        "name": note.name,
        "about": note.about,
        "subject": note.subject,
        "username": note.username
    }
    
    try:
        newNote = notedb.insert(noter)
        return newNote
    except:
        return({
            "status": 500,
            "message": "Some Error Occurred."
        })
        
class UpdateNote(BaseModel):
    name: str
    about: str
        
@app.put("/api/note/{key}")
def createproject(key: str, updatenote: UpdateNote, Authorization: Optional[str] = Header(None)):
    
    if validateToken(Authorization) is False:
        return {
            "status": 401,
            "message": "Invalid Token"
        }
    
    notedb = deta.Base("Notecaster_Note")
    
    try:
        theNote = notedb.get(key)
        theNote['name'] = updatenote.name
        theNote['about'] = updatenote.about
        theNote = notedb.put(theNote)
        return theNote
    except:
        return({
            "status": 404,
            "message": "Note Does not Exist"
        })
        
@app.get("/api/notes/{subjectID}")
def getnotes(subjectID: str, Authorization: Optional[str] = Header(None)):
    
    if validateToken(Authorization) is False:
        return {
            "status": 401,
            "message": "Invalid Token"
        }
    
    notedb = deta.Base("Notecaster_Note")
    allNotes = next(notedb.fetch({"subject": subjectID}))
    return allNotes

@app.delete("/api/note/{key}")
def getproject(key: str, Authorization: Optional[str] = Header(None)):
    
    if validateToken(Authorization) is False:
        return {
            "status": 401,
            "message": "Invalid Token"
        }
        
    try:
        notedb = deta.Base("Notecaster_Note")
        notedb.delete(key)
        return ({
            "status": 203,
            "message": "Deleted Successfully."
        })
    
    except:
        return({
            "status": 404,
            "message": "Note Does not Exist"
        })
        
@app.get("/api/note/{key}")
def getnote(key: str, Authorization: Optional[str] = Header(None)):
    
    if validateToken(Authorization) is False:
        return {
            "status": 401,
            "message": "Invalid Token"
        }
    
    try:
        notedb = deta.Base("Notecaster_Note")
        theNote = notedb.get(key)
        if theNote is None:
            return({
                "status": 404,
                "message": "Note Does not Exist"
            })
        return theNote
    
    except:
        return({
            "status": 404,
            "message": "Note Does not Exist"
        })
        
class UpdateNoteDoc(BaseModel):
    content: str        
        
@app.put("/api/updatenotedoc/{noteKey}")
def updateNoteDoc(noteKey: str, docData: UpdateNoteDoc, Authorization: Optional[str] = Header(None)):
    
    if validateToken(Authorization) is False:
        return {
            "status": 401,
            "message": "Invalid Token"
        }
    
    notedb = deta.Base("Notecaster_Note")
    theNote = notedb.get(noteKey)
    if theNote is None:
        return({
            "status": 404,
            "message": "Note Does not Exist"
        })
    theNote['content'] = docData.content
    theNote = notedb.put(theNote)
    return theNote


#Flashcards APIs

class TypeOneCard(BaseModel):
    noteText: str
    imageLink: str
    subject: str
    
class TypeTwoCard(BaseModel):
    question: str
    questionImageLink: str
    answer: str
    answerImageLink: str
    subject: str

@app.post("/api/flashcards/type1")
def createCardOne(card: TypeOneCard, Authorization: Optional[str] = Header(None)):
    
    if validateToken(Authorization) is False:
        return {
            "status": 401,
            "message": "Invalid Token"
        }
    
    noteText = card.noteText
    imageLink = card.imageLink
    subject = card.subject
    
    carddb = deta.Base("Notecaster_Card")
    
    createCard = {
        "type": 1,
        "noteText": noteText,
        "imageLink": imageLink,
        "subject": subject
    }
    
    try:
        newCard = carddb.insert(createCard)
        return newCard
    
    except:
        return({
            "status": 500,
            "message": "Some Error Occurred."
        })
        
@app.post("/api/flashcards/type2")
def createCardTwo(card: TypeTwoCard, Authorization: Optional[str] = Header(None)):
    
    if validateToken(Authorization) is False:
        return {
            "status": 401,
            "message": "Invalid Token"
        }
    
    question = card.question
    questionImageLink = card.questionImageLink
    answer = card.answer
    answerImageLink = card.answerImageLink
    subject = card.subject
    
    carddb = deta.Base("Notecaster_Card")
    
    createCard = {
        "type": 2,
        "question": question,
        "questionImageLink": questionImageLink,
        "answer": answer,
        "answerImageLink": answerImageLink,
        "subject": subject
    }
    
    try:
        newCard = carddb.insert(createCard)
        return newCard
    
    except:
        return({
            "status": 500,
            "message": "Some Error Occurred."
        })
        
@app.get("/api/flashcards/{subjectID}")
def getCards(subjectID: str, Authorization: Optional[str] = Header(None)):
    
    if validateToken(Authorization) is False:
        return {
            "status": 401,
            "message": "Invalid Token"
        }
    
    carddb = deta.Base("Notecaster_Card")
    allCards = next(carddb.fetch({"subject": subjectID}))
    return allCards

@app.get("/api/flashcard/{key}")
def getCard(key: str, Authorization: Optional[str] = Header(None)):
    
    if validateToken(Authorization) is False:
        return {
            "status": 401,
            "message": "Invalid Token"
        }
    
    carddb = deta.Base("Notecaster_Card")
    theCard = carddb.get(key)
    if theCard is None:
        return({
            "status": 404,
            "message": "Card Does not Exist"
        })
    return theCard

@app.delete("/api/flashcard/{key}")
def deleteCard(key: str, Authorization: Optional[str] = Header(None)):
    
    if validateToken(Authorization) is False:
        return {
            "status": 401,
            "message": "Invalid Token"
        }
    
    try:
        carddb = deta.Base("Notecaster_Card")
        carddb.delete(key)
        return ({
            "status": 203,
            "message": "Deleted Successfully."
        })
    except:
        return({
            "status": 404,
            "message": "Card Does not Exist"
        })

class UpdateTypeOneCard(BaseModel):
    noteText: str
    imageLink: str

@app.put("/api/flashcard/type1/{key}")
def updateCardOne(key: str, card: UpdateTypeOneCard, Authorization: Optional[str] = Header(None)):
    
    if validateToken(Authorization) is False:
        return {
            "status": 401,
            "message": "Invalid Token"
        }
    
    try:
        carddb = deta.Base("Notecaster_Card")
        theCard = carddb.get(key)
        theCard['noteText'] = card.noteText
        theCard['imageLink'] = card.imageLink
        theCard = carddb.put(theCard)
        return theCard
    
    except:
        return({
            "status": 404,
            "message": "Card Does not Exist"
        })
        
class UpdateTypeTwoCard(BaseModel):
    question: str
    questionImageLink: str
    answer: str
    answerImageLink: str
    
@app.put("/api/flashcard/type2/{key}")
def updateCardTwo(key: str, card: UpdateTypeTwoCard, Authorization: Optional[str] = Header(None)):
    
    if validateToken(Authorization) is False:
        return {
            "status": 401,
            "message": "Invalid Token"
        }
    
    try:
        carddb = deta.Base("Notecaster_Card")
        theCard = carddb.get(key)
        theCard['question'] = card.question
        theCard['questionImageLink'] = card.questionImageLink
        theCard['answer'] = card.answer
        theCard['answerImageLink'] = card.answerImageLink
        theCard = carddb.put(theCard)
        return theCard
    
    except:
        return({
            "status": 404,
            "message": "Card Does not Exist"
        })


#Sticky Notes
#unlimited sticky notes w.r.t. subject

class StickyNote(BaseModel):
    username: str
    subjectID: str
    data: str
    imageLink: str
    backgroundColor: str
    imageColor: str

@app.post("/api/stickynotes")
def createproject(stickyNote: StickyNote, Authorization: Optional[str] = Header(None)):
    
    if validateToken(Authorization) is False:
        return {
            "status": 401,
            "message": "Invalid Token"
        }
    
    username = stickyNote.username
    subjectID = stickyNote.subjectID
    data = stickyNote.data
    imageLink = stickyNote.imageLink
    backgroundColor = stickyNote.backgroundColor
    imageColor = stickyNote.imageColor
    
    stickynotedb = deta.Base("Notecaster_StickyNote")
    
    createStickyNote = {
        "username": username,
        "subjectID": subjectID,
        "data": data,
        "imageLink": imageLink,
        "backgroundColor": backgroundColor,
        "imageColor": imageColor
    }
    
    try:
        newStickyNote = stickynotedb.insert(createStickyNote)
        return newStickyNote
    
    except:
        return({
            "status": 500,
            "message": "Some Error Occurred."
        })
     
@app.get("/api/stickynotes/{subjectID}")
def getprojects(subjectID: str, Authorization: Optional[str] = Header(None)):
    
    if validateToken(Authorization) is False:
        return {
            "status": 401,
            "message": "Invalid Token"
        }
    
    stickynotedb = deta.Base("Notecaster_StickyNote")
    allStickyNotes = next(stickynotedb.fetch({"subjectID": subjectID}))
    return allStickyNotes

@app.get("/api/stickynote/{key}")
def getprojects(key: str, Authorization: Optional[str] = Header(None)):
    
    if validateToken(Authorization) is False:
        return {
            "status": 401,
            "message": "Invalid Token"
        }
    
    stickynotedb = deta.Base("Notecaster_StickyNote")
    theStickyNote = stickynotedb.get(key)
    if theStickyNote is None:
        return({
            "status": 404,
            "message": "Sticky Note Does not Exist"
        })
    return theStickyNote

@app.delete("/api/stickynote/{key}")
def deleteCard(key: str, Authorization: Optional[str] = Header(None)):
    
    if validateToken(Authorization) is False:
        return {
            "status": 401,
            "message": "Invalid Token"
        }
    
    try:
        stickynotedb = deta.Base("Notecaster_StickyNote")
        stickynotedb.delete(key)
        return ({
            "status": 203,
            "message": "Deleted Successfully."
        })
    except:
        return({
            "status": 404,
            "message": "Sticky Note Does not Exist"
        })
        
class UpdateStickyNote(BaseModel):
    data: str
    imageLink: str
    backgroundColor: str
    imageColor: str
    
@app.put("/api/stickynote/{key}")
def updateStickyNote(key: str, stickyNote: UpdateStickyNote, Authorization: Optional[str] = Header(None)):
    
    if validateToken(Authorization) is False:
        return {
            "status": 401,
            "message": "Invalid Token"
        }
    
    try:
        stickynotedb = deta.Base("Notecaster_StickyNote")
        theStickyNote = stickynotedb.get(key)
        theStickyNote['data'] = stickyNote.data
        theStickyNote['imageLink'] = stickyNote.imageLink
        theStickyNote['backgroundColor'] = stickyNote.backgroundColor
        theStickyNote['imageColor'] = stickyNote.imageColor
        theStickyNote = stickynotedb.put(theStickyNote)
        return theStickyNote
    
    except:
        return({
            "status": 404,
            "message": "Card Does not Exist"
        })