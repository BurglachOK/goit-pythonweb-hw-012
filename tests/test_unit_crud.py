import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from datetime import date
import crud
import models
from schemas import ContactCreate, ContactUpdate
from db import get_db

def test_get_db_yields_session():
    generator = get_db()
    db_session = next(generator)
    assert db_session is not None
    with pytest.raises(StopIteration):
        next(generator)

def test_get_contacts(db_session):
    user = models.User(id=1, email="user@test.com")
    contact = models.Contact(first_name="Ivan", last_name="Sirko", email="ivan@test.com", user_id=user.id)
    db_session.add(contact)
    db_session.commit()

    contacts = crud.get_contacts(db=db_session, user=user)
    assert len(contacts) > 0
    assert contacts[0].first_name == "Ivan"

def test_create_contact(db_session):
    user = models.User(id=2, email="user2@test.com")
    contact_schema = ContactCreate(
        first_name="Serhii", last_name="Buriak", 
        email="stepan@test.com", phone="+38000", birthday=None, additional_data=None
    )
    new_contact = crud.create_contact(db=db_session, contact=contact_schema, user=user)
    assert new_contact.id is not None
    assert new_contact.first_name == "Serhii"

def test_update_contact(db_session):
    user = models.User(id=3, email="user3@test.com")
    contact = models.Contact(first_name="OldName", last_name="Petrenko", email="old@test.com", user_id=user.id)
    db_session.add(contact)
    db_session.commit()

    contact_update_schema = ContactUpdate(
        first_name="NewName", last_name="Petrenko", 
        email="new_email@test.com", phone="+38000", birthday=None, additional_data=None
    )

    updated_contact = crud.update_contact(db=db_session, contact_id=contact.id, contact=contact_update_schema, user=user)

    assert updated_contact.first_name == "NewName"
    assert updated_contact.email == "new_email@test.com"


def test_delete_contact(db_session):
    user = models.User(id=4, email="user4@test.com")
    contact = models.Contact(first_name="ToDelete", last_name="Ivanov", email="delete@test.com", user_id=user.id)
    db_session.add(contact)
    db_session.commit()

    result = crud.delete_contact(db=db_session, contact_id=contact.id, user=user)

    assert result is not None

    deleted_contact = db_session.query(models.Contact).filter(models.Contact.id == contact.id).first()
    assert deleted_contact is None

def test_get_upcoming_birthdays(db_session):
    user = models.User(id=5, email="user5@test.com")
    from datetime import date
    today = date.today()
    bday = date(1990, today.month, today.day)
    
    contact = models.Contact(first_name="Bday", last_name="User", email="bday@test.com", birthday=bday, user_id=user.id)
    db_session.add(contact)
    db_session.commit()

    results = crud.get_upcoming_birthdays(db=db_session, user=user)
    assert len(results) == 1
    assert results[0].first_name == "Bday"