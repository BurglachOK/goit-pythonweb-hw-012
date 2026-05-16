from datetime import date, timedelta
from typing import List, Optional
from sqlalchemy import or_, extract, and_
from sqlalchemy.orm import Session
from models import Contact
import models
from schemas import ContactCreate, ContactUpdate

def get_contacts(db: Session, user: models.User, skip: int = 0, limit: int = 100) -> List[Contact]:
    """
    Retrieve a list of contacts belonging to a specific user with pagination.

    :param db: The database session instance.
    :type db: Session
    :param user: The currently authenticated user.
    :type user: models.User
    :param skip: Number of records to skip (for pagination), defaults to 0.
    :type skip: int
    :param limit: Maximum number of records to return, defaults to 100.
    :type limit: int
    :return: A list of Contact database models.
    :rtype: List[Contact]
    """
    return db.query(Contact).filter(Contact.user_id == user.id).offset(skip).limit(limit).all()

def get_contact(db: Session, contact_id: int, user: models.User) -> Optional[Contact]:
    """
    Retrieve a single contact by its ID, ensuring it belongs to the authenticated user.

    :param db: The database session instance.
    :type db: Session
    :param contact_id: The unique identifier of the contact.
    :type contact_id: int
    :param user: The currently authenticated user.
    :type user: models.User
    :return: The Contact model if found and owned by the user, else None.
    :rtype: Optional[Contact]
    """
    return db.query(Contact).filter(and_(Contact.id == contact_id, Contact.user_id == user.id)).first()

def create_contact(db: Session, contact: ContactCreate, user: models.User) -> Contact:
    """
    Create a new contact record linked to the authenticated user.

    :param db: The database session instance.
    :type db: Session
    :param contact: The schema containing validated creation data.
    :type contact: ContactCreate
    :param user: The currently authenticated user.
    :type user: models.User
    :return: The newly created Contact object from the database.
    :rtype: Contact
    """
    db_contact = Contact(**contact.model_dump(), user_id=user.id)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

def update_contact(db: Session, contact_id: int, contact: ContactUpdate, user: models.User) -> Optional[Contact]:
    """
    Perform a partial update (PATCH) on an existing contact record if owned by the user.

    :param db: The database session instance.
    :type db: Session
    :param contact_id: The unique identifier of the contact to update.
    :type contact_id: int
    :param contact: The schema containing fields to update.
    :type contact: ContactUpdate
    :param user: The currently authenticated user.
    :type user: models.User
    :return: The updated Contact instance, or None if not found.
    :rtype: Optional[Contact]
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
    Delete a contact record from the database, enforcing user ownership.

    :param db: The database session instance.
    :type db: Session
    :param contact_id: The identifier of the contact to delete.
    :type contact_id: int
    :param user: The currently authenticated user.
    :type user: models.User
    :return: The deleted Contact instance if successful, or None if access denied/not found.
    :rtype: Optional[Contact]
    """
    db_contact = db.query(Contact).filter(and_(Contact.id == contact_id, Contact.user_id == user.id)).first()
    if db_contact:
        db.delete(db_contact)
        db.commit()
    return db_contact

def search_contacts(db: Session, query: str, user: models.User) -> List[Contact]:
    """
    Search contacts by first name, last name, or email matching a substring case-insensitively.

    :param db: The database session instance.
    :type db: Session
    :param query: The search query string.
    :type query: str
    :param user: The currently authenticated user.
    :type user: models.User
    :return: A list of matching Contact records.
    :rtype: List[Contact]
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
    Fetch all contacts whose birthdays occur within the next 7 days.

    :param db: The database session instance.
    :type db: Session
    :param user: The currently authenticated user.
    :type user: models.User
    :return: A list of contacts with upcoming birthdays.
    :rtype: List[Contact]
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