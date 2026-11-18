from fastapi import FastAPI,Query,Path,Body,UploadFile
from pydantic import BaseModel,Field
from uuid import uuid4,UUID
from typing import Annotated, List, Optional

class user_template(BaseModel):
    first_name:str
    last_name:str
    age:int
    email:str
    is_active:bool

class User(user_template):
    user_id:UUID=Field(default_factory=uuid4,alias="user_id")

app=FastAPI()

users=dict()

@app.post("/")
def root(file:UploadFile):
    return {
        "filename": file.filename,
        "message": "File uploaded successfully"
    }

@app.post("/users/new_user")
def create_user(user:user_template):
    new_user=User(**user.model_dump())
    users[new_user.user_id] = new_user
    return new_user


@app.get("/users/all")
def get_users():
    return users

@app.get("/users/{user_id}")
def get_user(user_id: UUID):
    return users.get(user_id)

@app.put("/users/{user_id}")
def update_user(user_id: UUID, user: user_template):
    users[user_id] = User(**user.model_dump(), user_id=user_id)
    return users[user_id]

@app.delete("/users/{user_id}")
def delete_user(user_id: UUID):
    if user_id in users.keys():
        del users[user_id]
        return {"message": "User deleted successfully"}