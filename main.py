from faker import Faker
from fastapi import FastAPI, Depends, HTTPException, status, Query, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List
from jose import JWTError, jwt
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import cloudinary
import cloudinary.uploader
from sqlalchemy.exc import IntegrityError
from db import get_db, engine
from models import Base
import models
import crud
import auth
from auth import get_current_user, SECRET_KEY, ALGORITHM
from schemas import (
    ContactResponse, ContactCreate, ContactUpdate, 
    UserCreate, UserResponse, Token)
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
from services.email import send_verification_email
from fastapi.security import OAuth2PasswordRequestForm
load_dotenv()
import os
from schemas import RequestEmail, ResetPassword
from auth import RoleChecker, redis_client
from services.email import send_reset_password_email
from alembic.config import Config, command
limiter = Limiter(key_func=get_remote_address)
fake = Faker()

try:
    print("Running Alembic database migrations...")
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    print("Migrations applied successfully!")
except Exception as e:
    print(f"Alembic migration failed or tables already exist: {e}")

app = FastAPI(
    title="Premium Contacts API",
    description="A professional API for managing personal and business contacts",
    docs_url="/docs",
    redoc_url="/redoc",
    version="1.1.0"
)

cloudinary.config( 
    cloud_name = os.getenv("CLOUDINARY_NAME"), 
    api_key = os.getenv("CLOUDINARY_API_KEY"), 
    api_secret = os.getenv("CLOUDINARY_API_SECRET"),
    secure = True
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Auth endpoints ---

@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Auth"])
async def register(user: UserCreate, request: Request, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        if not db_user.confirmed:
            print(f"DEBUG: Removing unverified user {user.email} to allow re-registration.", flush=True)
            db.delete(db_user)
            db.commit()
        else:
            raise HTTPException(status_code=409, detail="Email already registered")
    
    assigned_role = "user"
    if user.admin_token and user.admin_token.strip() and user.admin_token != "string":
        expected_token = os.getenv("ADMIN_REGISTRATION_TOKEN")
        if user.admin_token == expected_token:
            assigned_role = "admin"
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Invalid admin registration token"
            )
            
    hashed_password = auth.get_password_hash(user.password)
    

    new_user = models.User(
        email=user.email, 
        username=user.username, 
        password=hashed_password, 
        role=assigned_role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    base_url = str(request.base_url)
    await send_verification_email(user.email, user.username, base_url)
    
    return new_user

@app.post("/auth/login", response_model=Token, tags=["Auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not user.confirmed:
        raise HTTPException(status_code=403, detail="Email not confirmed")
    
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/confirm/{token}", tags=["Auth"])
async def confirm_email(token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=400, detail="Invalid token")
        
        user = db.query(models.User).filter(models.User.email == email).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.confirmed = True
        db.commit()
        return {"message": "Email confirmed successfully"}
    except JWTError:
        raise HTTPException(status_code=400, detail="Token is invalid or expired")


@app.post("/auth/request-password-reset", tags=["Auth"])
async def request_password_reset(body: RequestEmail, request: Request, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if not user:
        return {"message": "If the email exists, a reset link has been sent."}
    
    base_url = str(request.base_url)
    await send_reset_password_email(user.email, user.username, base_url)
    return {"message": "Password reset link sent to your email."}

@app.post("/auth/reset-password", tags=["Auth"])
async def reset_password(body: ResetPassword, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(body.token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("action") != "reset_password":
            raise HTTPException(status_code=400, detail="Invalid token action")
        email = payload.get("sub")
        
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.password = auth.get_password_hash(body.new_password)
        db.commit()
        redis_client.delete(f"user:{email}")
        
        return {"message": "Password reset successfully."}
    except JWTError:
        raise HTTPException(status_code=400, detail="Token is invalid or expired")
    
# --- Contacts endpoints ---

@app.post("/contacts/seed", status_code=status.HTTP_201_CREATED)
async def seed_contacts(
    count: int = Query(default=100, ge=1, le=250),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Generates random contacts for the currently logged-in user.
    """
    for _ in range(count):
        new_contact = models.Contact(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.unique.email(),
            phone=fake.phone_number()[:20],
            birthday=fake.date_of_birth(minimum_age=20, maximum_age=65),
            additional_data=fake.sentence(nb_words=4),
            user_id=current_user.id
        )
        db.add(new_contact)
    
    db.commit()
    return {"message": f"Created {count} contacts for {current_user.email}"}


@app.post("/contacts/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
def create_new_contact(
    contact: ContactCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        return crud.create_contact(db=db, contact=contact, user=current_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contact with this email already exists"
        )

@app.get("/contacts/", response_model=List[ContactResponse], tags=["Contacts"])
def read_contacts(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)):
    return crud.get_contacts(db=db, user=current_user, skip=skip, limit=limit)

@app.get("/contacts/search", response_model=List[ContactResponse], tags=["Contacts"])
def search_for_contacts(
    query: str = Query(..., min_length=1), 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.search_contacts(db=db, query=query, user=current_user)

@app.get("/contacts/birthdays", response_model=List[ContactResponse], tags=["Contacts"])
def get_birthdays(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.get_upcoming_birthdays(db=db, user=current_user)

@app.get("/contacts/{contact_id}", response_model=ContactResponse, tags=["Contacts"])
def read_single_contact(
    contact_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_contact = crud.get_contact(db=db, contact_id=contact_id, user=current_user)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return db_contact

@app.patch("/contacts/{contact_id}", response_model=ContactResponse, tags=["Contacts"])
def update_existing_contact(
    contact_id: int, 
    contact: ContactUpdate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_contact = crud.update_contact(db=db, contact_id=contact_id, contact=contact, user=current_user)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found or access denied")
    return db_contact

@app.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Contacts"])
def delete_existing_contact(
    contact_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_contact = crud.delete_contact(db=db, contact_id=contact_id, user=current_user)
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found or access denied")
    return None

# --- User endpoints ---

@app.get("/users/me", tags=["Users"])
@limiter.limit("5/minute")
async def read_users_me(
    request: Request, 
    current_user: models.User = Depends(get_current_user)
):
    return current_user

@app.patch("/users/avatar", tags=["Users"])
async def update_avatar(
    file: UploadFile = File(...), 
    current_user: models.User = Depends(RoleChecker(["admin"])),
    db: Session = Depends(get_db)
):
    r = cloudinary.uploader.upload(file.file, public_id=f"avatars/{current_user.email}", overwrite=True)
    avatar_url = r.get("secure_url")
    current_user.avatar = avatar_url
    db.commit()
    
    redis_client.delete(f"user:{current_user.email}")
    
    return {"avatar_url": avatar_url}

@app.get("/")
@app.get("")
def read_root():
    print({"message": "Welcome to the Premium Contacts API! Made by Serhii Buriak."})
    return RedirectResponse(url="/docs")