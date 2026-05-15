from datetime import date, timedelta
from typing import List, Optional
from sqlalchemy import or_, extract, and_
from sqlalchemy.orm import Session
from models import Contact
import models
from schemas import ContactCreate, ContactUpdate

def get_contacts(db: Session, user: models.User, skip: int = 0, limit: int = 100):
    """
    Gets a list of contacts only for the current user with pagination support.
    """
    return db.query(Contact).filter(Contact.user_id == user.id).offset(skip).limit(limit).all()

def get_contact(db: Session, contact_id: int, user: models.User) -> Optional[Contact]:
    """
    Gets a specific contact by ID, checking ownership by the current user.
    """
    return db.query(Contact).filter(and_(Contact.id == contact_id, Contact.user_id == user.id)).first()

def create_contact(db: Session, contact: ContactCreate, user: models.User):
    """
    Creates a new contact, automatically linking it to the current user's ID.
    """
    db_contact = Contact(**contact.model_dump(), user_id=user.id)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def update_contact(db: Session, contact_id: int, contact: ContactUpdate, user: models.User) -> Optional[Contact]:
    """
    Updates an existing contact (PATCH), if it belongs to the current user.
    """
    db_contact = db.query(Contact).filter(and_(Contact.id == contact_id, Contact.user_id == user.id)).first()
    if db_contact:
        update_data = contact.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_contact, key, value)
        
        db.commit()
        db.refresh(db_contact)
    return db_contact

def delete_contact(db: Session, contact_id: int, user: models.User) -> Optional[Contact]:
    """
    Deletes a contact from the database if it belongs to the current user.
    """
    db_contact = db.query(Contact).filter(and_(Contact.id == contact_id, Contact.user_id == user.id)).first()
    if db_contact:
        db.delete(db_contact)
        db.commit()
    return db_contact

def search_contacts(db: Session, query: str, user: models.User) -> List[Contact]:
    """
    Searches for contacts by name, last name, or email, but only among the current user's records.
    """
    return db.query(Contact).filter(
        and_(
            Contact.user_id == user.id,
            or_(
                Contact.first_name.ilike(f"%{query}%"),
                Contact.last_name.ilike(f"%{query}%"),
                Contact.email.ilike(f"%{query}%")
            )
        )
    ).all()

def get_upcoming_birthdays(db: Session, user: models.User) -> List[Contact]:
    """
    Gets a list of contacts for the current user who have birthdays within the next 7 days.
    """
    today = date.today()
    days_range = []
    
    for i in range(8):
        future_date = today + timedelta(days=i)
        days_range.append((future_date.month, future_date.day))

    date_filters = [
        and_(
            extract('month', Contact.birthday) == m,
            extract('day', Contact.birthday) == d
        ) for m, d in days_range
    ]

    return db.query(Contact).filter(
        and_(
            Contact.user_id == user.id,
            or_(*date_filters)
        )
    ).all()