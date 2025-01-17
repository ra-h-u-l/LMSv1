from .database import db
from datetime import datetime, timedelta

#1 --------------------------> login_credentials_table <--------------------------------
class LoginCredentials(db.Model):
    username = db.Column(db.String(20), primary_key = True)
    password = db.Column(db.String(16), nullable = False)
    type = db.Column(db.String(), default="user")



#2 ---------------------> section_table <-------------------
class Sections(db.Model):
    section_id = db.Column(db.String(10), primary_key = True)
    section_name = db.Column(db.String(50), nullable = False)
    date_created = db.Column(db.DateTime(), default = datetime.now)
    last_updated = db.Column(db.DateTime(), default = datetime.now)
    description = db.Column(db.String(200))
    # Relationship
    books = db.relationship("Books", backref="section", cascade="all, delete-orphan, save-update")



#3 ------------------------> book_table <-------------------------
class Books(db.Model):
    book_id = db.Column(db.String(10), primary_key = True)
    book_name = db.Column(db.String(50), nullable = False)
    date_created = db.Column(db.DateTime(), default = datetime.now)
    last_updated = db.Column(db.DateTime(), default = datetime.now)
    section_id = db.Column(db.String(), db.ForeignKey("sections.section_id"), nullable = False)
    content = db.Column(db.String(), nullable = False)            # few lines of text
    authors = db.Column(db.String(), nullable = False)
    total_copies = db.Column(db.Integer(), nullable = False)
    available_copies = db.Column(db.Integer())
    issued_copies = db.Column(db.Integer())
    sold_copies = db.Column(db.Integer())
    book_price = db.Column(db.Integer(), default = 0)
    # Relationships
    requested_books = db.relationship("RequestedBooks", backref="books", cascade="all, delete-orphan, save-update")
    currently_issued_books = db.relationship("CurrentlyIssuedBooks", backref="books", cascade="all, delete-orphan, save-update")
    sold_books = db.relationship("SoldBooks", backref="books", cascade="all, delete-orphan, save-update")



#4 -------------------------> requested_book_table <-----------------
class RequestedBooks(db.Model):
    book_id = db.Column(db.String(), db.ForeignKey("books.book_id"), primary_key = True)
    user_id = db.Column(db.String(), primary_key = True)
    date_requested = db.Column(db.DateTime(), default = datetime.now)
    days_requested = db.Column(db.Integer(), nullable = False)



#5 -----------------------> currently_issued_books <-------------------
class CurrentlyIssuedBooks(db.Model):
    book_id = db.Column(db.String(), db.ForeignKey("books.book_id"), primary_key = True)
    user_id = db.Column(db.String(), primary_key = True)
    date_requested = db.Column(db.DateTime())
    date_issued = db.Column(db.DateTime(), default = datetime.now)
    days_requested = db.Column(db.Integer(), nullable = False)


#6 ------------------> sold_books <-----------------
class SoldBooks(db.Model):
    book_id = db.Column(db.String(), db.ForeignKey("books.book_id"), primary_key = True)
    user_id = db.Column(db.String(), primary_key = True)
    date_sold = db.Column(db.DateTime(), default = datetime.now)



#7 -------------------------> user_book_history_table <-----------------
class UserBookHistory(db.Model):
    id = db.Column(db.Integer(), primary_key = True)
    book_id = db.Column(db.String(), nullable = False)
    user_id = db.Column(db.String(), nullable = False)
    book_name = db.Column(db.String(), nullable = False)
    days_requested = db.Column(db.Integer(), nullable = False)
    date_issued = db.Column(db.DateTime())
    is_issued = db.Column(db.Boolean())
    date_bought = db.Column(db.DateTime())
    is_bought = db.Column(db.Boolean(), default = False)