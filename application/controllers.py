from flask import Flask, render_template, request, redirect, url_for, send_file
from flask import current_app as app
from .model import *
from fpdf import FPDF
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("Agg")

# Auto revoke/return book after a certain time period.
revoke_time = 604800   # Note - revoke_time is in seconds | 604800 = 7 days


# Home Page ----------------------------------------------------------------------------------------
@app.route("/")
def home_page():
    return render_template("home.html")


# Librarian Login ----------------------------------------------------------------------------------
@app.route("/librarian_login", methods = ["GET", "POST"])
def librarian_login():
    # Credential check for login
    if request.method == "POST":
        u_name = request.form.get("username")
        pwd = request.form.get("password")
        this_user = LoginCredentials.query.filter_by(username = u_name).first()
        if this_user:
            if this_user.password == pwd and this_user.type == "admin":
                return redirect("/librarian_dashboard")
            else:
                return """Incorrect Credentials. Go to 
                            <a href="/librarian_login">Librarian Login</a>
                            <a href="/">Home</a>"""
        else:
            return """This account does not exists. Go to
                        <a href="/librarian_login">Librarian Login</a> or 
                        <a href="/">Home</a>"""
    return render_template("librarian_login.html")


# Librarian Dashboard ---------------------------------------------------------------------------------
@app.route("/librarian_dashboard", methods = ["GET", "POST"])
def librarian_dashboard():
    if request.method == "POST":
        # Logout button action
        user_logout = request.form.get("logout")
        if user_logout == "logout":
            return redirect("/librarian_login")

        # Add Section button action 
        add_section = request.form.get("add-section")
        if add_section == "add-section":
            return redirect("/add_section")

        # Add Book button action
        add_book = request.form.get("add-book")
        if add_book == "add-book":
            return redirect("/add_book")
        
        # Librarian Search - Redirecting to its endpoint
        if "search" == request.form.get("search"):
            word = request.form.get("search-bar-area")
            return redirect(f"/librarian_search_result/{word}")
            
        
        # Cancel book request
        to_cancel_requests = request.form.get("cancel-request")
        if to_cancel_requests:
            cancel_request = to_cancel_requests.split("*")
            # delete record from requested books table
            to_delete = RequestedBooks.query.filter_by(book_id = cancel_request[1], user_id = cancel_request[0]).first()
            db.session.delete(to_delete)
            db.session.commit()
            return redirect(url_for("librarian_dashboard"))

        # Issue/Grant book
        to_grant_requests = request.form.get("grant-request")
        if to_grant_requests:
            grant_request = to_grant_requests.split("*")
            # update available copies in book table
            this_book = Books.query.get(grant_request[1])
            this_book.available_copies = this_book.available_copies - 1
            this_book.issued_copies = this_book.issued_copies + 1
            book_in_requested_book_table = RequestedBooks.query.filter_by(book_id = grant_request[1], user_id = grant_request[0]).first()
            grant = CurrentlyIssuedBooks(book_id = book_in_requested_book_table.book_id,
                                            user_id = book_in_requested_book_table.user_id,
                                            date_requested = book_in_requested_book_table.date_requested,
                                            days_requested = book_in_requested_book_table.days_requested)
            db.session.add(grant)
            # Adding record to user book history table
            record_for_user_book_history = UserBookHistory(book_id = this_book.book_id,
                                                            user_id = book_in_requested_book_table.user_id,
                                                            book_name = this_book.book_name,
                                                            days_requested = 7,
                                                            date_issued = datetime.now(),
                                                            is_issued = True)
            db.session.add(record_for_user_book_history)
            db.session.delete(book_in_requested_book_table)
            db.session.commit()
            return redirect(url_for("librarian_dashboard"))            
    
    # Time Now
    time_now = datetime.now()
    seven_days = timedelta(days=7)

    # To fetch recently added sections on Librarian dashboard
    recent_sections = Sections.query.order_by(Sections.date_created.desc()).limit(5).all()

    # To fetch recently added books on Librarian dashboard
    recent_books = Books.query.order_by(Books.date_created.desc()).limit(5).all()

    # Requested Books list on Librarian dashboard
    requested_books = RequestedBooks.query.order_by(RequestedBooks.date_requested.asc()).all()

    # List of currently issued books
    currently_issued_book = CurrentlyIssuedBooks.query.order_by(CurrentlyIssuedBooks.date_issued.desc()).all()

    # List of Sold Books
    sold_books = SoldBooks.query.order_by(SoldBooks.date_sold.desc()).all()

    # Auto revoke/return book after a certain time period.
    # revoke_time = 30   # Note - revoke_time is in seconds. defined at top
    for book in currently_issued_book:
        if (time_now.timestamp() - book.date_issued.timestamp()) >= revoke_time:
            # update available copies and issued copies in book table
            book_in_book_table = Books.query.get(book.book_id)
            book_in_book_table.available_copies = book_in_book_table.available_copies + 1
            book_in_book_table.issued_copies = book_in_book_table.issued_copies - 1
            # delete record from currently books table
            db.session.delete(book)
            db.session.commit()

    return render_template("librarian_dashboard.html",
                            recent_sections = recent_sections,
                            recent_books = recent_books,
                            requested_books = requested_books,
                            currently_issued_book = currently_issued_book,
                            time_now = time_now,
                            seven_days = seven_days,
                            sold_books = sold_books)


# Add Section - by Librarian ---------------------------------------------------------------------------
@app.route("/add_section", methods = ["GET", "POST"])
def add_section():
    if request.method == "POST":
        section_id = request.form.get("section-id")
        section_name = request.form.get("section-name")
        section_description = request.form.get("section-description")
        this_section = Sections.query.filter_by(section_id = section_id).first()
        if this_section:
            return "Section Id already associated with a particular section. Please try a different one."
        else:
            new_section = Sections(section_id = section_id,
                                    section_name = section_name,
                                    description = section_description)
            db.session.add(new_section)
            db.session.commit()
            return redirect("/librarian_dashboard")
    return render_template("add_section.html")


# Add Book - by Librarian ---------------------------------------------------------------------------
@app.route("/add_book", methods = ["GET", "POST"])
def add_book():
    section_list = Sections.query.all()
    if request.method == "POST":
        book_id = request.form.get("book-id")
        book_name = request.form.get("book-name")
        section_id = request.form.get("section-id")
        content = request.form.get("book-content")
        authors = request.form.get("book-authors")
        total_copies = request.form.get("book-total-copies")
        available_copies = total_copies
        issued_copies = 0
        sold_copies = 0
        price = request.form.get("price")
        this_book = Books.query.filter_by(book_id = book_id).first()
        if this_book:
            return f"The book with id: {book_id} already exists."
        else:
            new_book = Books(book_id = book_id, 
                            book_name = book_name,
                            section_id = section_id,
                            content = content,
                            authors = authors,
                            total_copies = total_copies,
                            available_copies = available_copies,
                            issued_copies = issued_copies,
                            sold_copies = sold_copies,
                            book_price = price)
            db.session.add(new_book)
            db.session.commit()
            return redirect("/librarian_dashboard")
    return render_template("add_book.html", section_list = section_list)

# Update Book - by Libraraian ------------------------------------------------------------------------
@app.route("/update_book/<book_id>", methods = ["GET", "POST"])
def update_book(book_id):
    current_book = Books.query.get(book_id)
    # print("Testing-------",current_book,book_id)
    section_list = Sections.query.all()
    if request.method == "POST":
        # current_book.book_id = request.form.get("book-id")
        current_book.book_name = request.form.get("book-name")
        current_book.book_name = request.form.get("book-name")
        current_book.section_id = request.form.get("section-id")
        current_book.content = request.form.get("book-content")
        current_book.content = request.form.get("book-content")
        current_book.authors = request.form.get("book-authors")
        current_book.authors = request.form.get("book-authors")
        total = request.form.get("book-total-copies")
        available = request.form.get("book-available-copies")
        current_book.book_price = request.form.get("price")
        current_book.last_updated = datetime.now()
        if int(total) == (int(available) + current_book.issued_copies + current_book.sold_copies):
            current_book.total_copies = int(total)
            current_book.available_copies = int(available)
            db.session.commit()
            db.session.close()
            return redirect("/all_books")
        else:
            db.session.rollback()
            db.session.close()
            return "Please enter correct entries in Total copies and Avaialable Copies"
    return render_template("update_book.html", book = current_book, section_list = section_list)



# Delete Book - by Librarian ------------------------------------------------------------------
@app.route("/delete_book/<book_id>", methods = ["GET", "POST"])
def delete_book(book_id):
    this_book = Books.query.get(book_id)
    try:
        db.session.delete(this_book)
        db.session.commit()
        return redirect("/librarian_dashboard")
    except:
        db.session.rollback()
        return redirect("/librarian_dashboard")
    finally:
        db.session.close()
    return redirect("/librarian_dashboard")


# Update Section - by Librarian ---------------------------------------------------------------
@app.route("/update_section/<section_id>", methods = ["GET", "POST"])
def update_section(section_id):
    this_section = Sections.query.get(section_id)
    if request.method == "POST":
        try:
            # this_section.section_id = request.form.get("section-id")
            this_section.section_name = request.form.get("section-name")
            this_section.last_updated = datetime.now()
            this_section.description = request.form.get("section-description")
            db.session.commit()
            db.session.close()
            return redirect("/all_sections")
        except:
            db.session.rollback()
            db.session.close()
            return redirect(f"/update_section/{section_id}")
    return render_template("update_section.html", this_section = this_section)


# Delete Section - by Librarian --------------------------------------------------------------
@app.route("/delete_section/<section_id>", methods = ["GET", "POST"])
def delete_section(section_id):
    this_section = Sections.query.get(section_id)
    try:
        db.session.delete(this_section)
        db.session.commit()
        return redirect("/librarian_dashboard")
    except:
        db.session.rollback()
        return redirect("/librarian_dashboard")
    finally:
        db.session.close()
    return redirect("/librarian_dashboard")


# All Sections -------------------------------------------------------------------------------
@app.route("/all_sections", methods = ["GET", "POST"])
def all_sections():
    all_sec = Sections.query.order_by(Sections.section_name.asc()).all()
    return render_template("all_sections.html", all_sec = all_sec)

# Individual Section View - Librarian -------------------------------------------------------------------------------
@app.route("/section_view/<section_id>", methods = ["GET", "POST"])
def section_view(section_id):
    this_section = Sections.query.filter_by(section_id = section_id).first()
    return render_template("view_section.html", this_section = this_section)

# All Books of a Section --------------------------------------------------------------------------
@app.route("/all_books_of/<section_id>", methods = ["GET", "POST"])
def all_books_of_this_section(section_id):
    this_section_all_books = Books.query.filter_by(section_id = section_id).all()
    return render_template("all_books_of_a_section_librarian.html",section_id = section_id, this_section_all_books = this_section_all_books)

# All Books -------------------------------------------------------------------------------
@app.route("/all_books", methods = ["GET", "POST"])
def all_books():
    all_bookz = Books.query.order_by(Books.book_name.asc()).all()
    return render_template("all_books.html", all_bookz = all_bookz)

# Individual Book View/Read - Librarian -------------------------------------------------------------
@app.route("/book_view/<book_id>", methods = ["GET", "POST"])
def book_view(book_id):
    this_book = Books.query.filter_by(book_id = book_id).first()
    return render_template("view_book.html", this_book = this_book)

# Librarian search result -------------------------------------------------------------------------------------------------------------
@app.route("/librarian_search_result/<word>", methods = ["GET", "POST"])
def librarian_search_result(word):
    book_list = Books.query.all()
    librarian_search_keyword = word
    keyword = librarian_search_keyword.lower()
    result_list = []
    for book in book_list:
        complete_string = book.book_name + book.authors + book.section.section_name
        complete_string_list = complete_string.split()
        complete_string_without_spaces = ""
        for element in complete_string_list:
            complete_string_without_spaces = complete_string_without_spaces + element
        final_search_string = complete_string_without_spaces.lower()
        if keyword in final_search_string:
            result_list.append((book.book_id, book.book_name, book.section.section_name, book.authors, book.section_id))
    
    return render_template("librarian_search_result.html", result_list = result_list)


# Librarian Statistics Page -------------------------------------------------------------------------
@app.route("/librarian_stats")
def librarian_stats():
    all_books = Books.query.all()
    books_per_section = []
    unique_sections = []
    available = []
    issued = []
    sold = []
    for book in all_books:
        if book is not None:
            books_per_section.append(book.section.section_name)
            if book.section.section_name not in unique_sections:
                unique_sections.append(book.section.section_name)
                available.append(book.available_copies)
                issued.append(book.issued_copies)
                sold.append(book.sold_copies)          
            else:
                available[unique_sections.index(book.section.section_name)] += book.available_copies
                issued[unique_sections.index(book.section.section_name)] += book.issued_copies
                sold[unique_sections.index(book.section.section_name)] += book.sold_copies
        else:
            books_per_section.append("Others")

    plt.clf()
    plt.hist(books_per_section)
    plt.title("Number of Unique Books per section")
    plt.savefig("static/lbps.png")

    plt.clf()
    plt.bar(unique_sections, available)
    plt.title("Total Available Books per Section")
    plt.savefig("static/ltabps.png")

    plt.clf()
    plt.bar(unique_sections, issued)
    plt.title("Total Issued Books per Section")
    plt.savefig("static/ltibps.png")

    plt.clf()
    plt.bar(unique_sections, sold)
    plt.title("Total Sold Books per Section")
    plt.savefig("static/ltsbps.png")

    return render_template("librarian_stats.html")

# User Registration ----------------------------------------------------------------------------------
@app.route("/register", methods = ["GET", "POST"])
def registration_page():
    if request.method == "POST":
        u_name = request.form.get("username")
        pwd = request.form.get("password")
        this_user = LoginCredentials.query.filter_by(username = u_name).first()
        if this_user:
            return "User already exists!"
        else:
            new_user = LoginCredentials(username = u_name, password = pwd)
            db.session.add(new_user)
            db.session.commit()
            return redirect("/login")

    return render_template("user_register.html")


# User Login -----------------------------------------------------------------------------------------
@app.route("/login", methods = ["GET", "POST"])
def login_page():
    if request.method == "POST":
        u_name = request.form.get("username")
        pwd = request.form.get("password")
        this_user = LoginCredentials.query.filter_by(username = u_name).first()
        if this_user:
            if this_user.password == pwd and this_user.type == "user":
                return redirect(f"/user_dashboard/{this_user.username}")
            else:
                return """Incorrect Credentials. Go to
                            <a href="/login">User Login</a> or 
                            <a href="/register">User Registration</a> or 
                            <a href="/">Home</a>"""
        else:
            return """This user does not exists. Go to 
                        <a href="/login">User Login</a> or 
                        <a href="/register">User Registration</a> or 
                        <a href="/">Home</a>"""
    return render_template("user_login.html")


# User Dashboard -------------------------------------------------------------------------------------
@app.route("/user_dashboard/<username>", methods = ["GET", "POST"])
def user_dashboard(username):
    this_user = LoginCredentials.query.get(username)
    if request.method == "POST":
        # Logout button action
        user_logout = request.form.get("logout")
        if user_logout == "logout":
            return redirect(url_for("login_page"))

        # Cancel requested book
        cancel_request = request.form.get("cancel-request")
        if cancel_request:
            this_book_id = request.form.get("cancel-request")
            # delete record from requested books table
            to_delete = RequestedBooks.query.filter_by(book_id = this_book_id, user_id = this_user.username).first()
            db.session.delete(to_delete)
            db.session.commit()
            return redirect(url_for("user_dashboard", username = this_user.username))

        # Return borrowed book
        return_book = request.form.get("return-book")
        if return_book:
            this_book_id = return_book
            to_return_book = CurrentlyIssuedBooks.query.filter_by(book_id = this_book_id, user_id = this_user.username).first()
            # update available copies and issued copies in book table
            book_in_book_table = Books.query.get(this_book_id)
            book_in_book_table.available_copies = book_in_book_table.available_copies + 1
            book_in_book_table.issued_copies = book_in_book_table.issued_copies - 1
            # delete record from currently books table
            db.session.delete(to_return_book)
            db.session.commit()
            return redirect(url_for("user_dashboard", username = this_user.username))

    # Time now
    time_now = datetime.now()
    seven_days = timedelta(days=7)
    
    # Pending Book Requests
    pending_books = RequestedBooks.query.filter_by(user_id = this_user.username).all()

    # Borrowed Books list
    borrowed_books = CurrentlyIssuedBooks.query.filter_by(user_id = this_user.username).all()

    # Bought Books list
    bought_books = SoldBooks.query.filter_by(user_id = this_user.username).all()

    # Recently read book list
    recently_read_books = UserBookHistory.query.order_by(UserBookHistory.date_issued.desc()).limit(5).all()

    # Auto revoke/return book after a certain time period.
    # revoke_time = 30   # Note - revoke_time is in seconds, defined at top
    for book in borrowed_books:
        if (time_now.timestamp() - book.date_issued.timestamp()) >= revoke_time:
            # update available copies and issued copies in book table
            book_in_book_table = Books.query.get(book.book_id)
            book_in_book_table.available_copies = book_in_book_table.available_copies + 1
            book_in_book_table.issued_copies = book_in_book_table.issued_copies - 1
            # delete record from currently books table
            db.session.delete(book)
            db.session.commit()

    return render_template("user_dashboard.html", time_now = time_now,
                                                    seven_days = seven_days,
                                                    username = this_user.username,
                                                    pending_books = pending_books,
                                                    borrowed_books = borrowed_books,
                                                    bought_books = bought_books,
                                                    recently_read_books = recently_read_books)

# User All Books View ------------------------------------------------------------------------------
@app.route("/user_dashboard/<username>/all_books", methods = ["GET", "POST"])
def user_all_books(username):
    books = Books.query.all()
    this_user = LoginCredentials.query.get(username)
    return render_template("user_all_books.html", books = books, username = this_user.username)

# User All Sections View------------------------------------------------------------------------------
@app.route("/user_dashboard/<username>/all_sections", methods = ["GET", "POST"])
def user_all_sections(username):
    sections = Sections.query.all()
    this_user = LoginCredentials.query.get(username)
    return render_template("user_all_sections.html", sections = sections, username = this_user.username)

# User Single Section View------------------------------------------------------------------------------
@app.route("/user_dashboard/<username>/<section_id>", methods = ["GET", "POST"])
def user_single_sections(username, section_id):
    books = Books.query.filter_by(section_id = section_id)
    this_user = LoginCredentials.query.get(username)
    return render_template("user_section_view.html", books = books, username = this_user.username)


# Request to Borrow a Book-------------------------------------------------------------------------
@app.route("/user_dashboard/<username>/borrow", methods = ["GET","POST"])
def borrow_request(username):
    this_user = LoginCredentials.query.get(username)
    if request.method == "POST":
        book_id = request.form.get("book_id")
        this_book = Books.query.get(book_id)
        user_id = this_user.username
        days_requested = 7
        requested_book_list = RequestedBooks.query.filter_by(user_id = user_id,
                                                                book_id = book_id).first()
        my_requested_book_count = RequestedBooks.query.filter(RequestedBooks.user_id == user_id).count()

        currently_issued_book_list = CurrentlyIssuedBooks.query.filter_by(user_id = user_id,
                                                                    book_id = book_id).first()
        my_currently_issued_book_count = CurrentlyIssuedBooks.query.filter(CurrentlyIssuedBooks.user_id == user_id).count()

        if requested_book_list or currently_issued_book_list:
            return "Already requested or borrowed this book."
        else:
            if this_book.available_copies > 0:
                if SoldBooks.query.filter_by(user_id = user_id, book_id = book_id).first():
                    return "You have already bought this book."
                else:
                    if my_requested_book_count + my_currently_issued_book_count >= 5:
                        return "Your (Issued Books + Requested Books) exceeds permissible limit of 5 books."
                    else:
                        # Adding record to requested books table
                        new_borrow_request = RequestedBooks(book_id = this_book.book_id,
                                                            user_id = user_id,
                                                            days_requested = days_requested)
                        db.session.add(new_borrow_request)
                        db.session.commit()
                        return redirect(f"/user_dashboard/{this_user.username}")
            else:
                return "This Book is not available now."
    return redirect(f"/user_dashboard/{this_user.username}")


# User Reads or Buy a particular book-------------------------------------------------------------------------
@app.route("/user_dashboard/<username>/read/<book_id>", methods = ["GET","POST"])
def user_reads_a_book(username, book_id):
    this_user = LoginCredentials.query.get(username)
    this_book = Books.query.get(book_id)
    already_bought = SoldBooks.query.filter_by(book_id = this_book.book_id, user_id = this_user.username).first()
    return render_template("user_read_or_buy_a_book.html", username = this_user.username,
                                                            book = this_book,
                                                            already_bought = already_bought)

# Payment -> User Buy a particular book-------------------------------------------------------------------------
@app.route("/payment_page/<username>/<book_id>/<book_price>", methods = ["GET", "POST"])
def payment(username, book_id, book_price):
    this_user = LoginCredentials.query.get(username)
    this_book = Books.query.get(book_id)
    if request.method == "POST":
        # Adding record to SoldBooks table
        bought_book = SoldBooks(user_id = this_user.username, book_id = book_id, date_sold = datetime.now())
        # Deleting record from CurrentlyIssuedBooks table
        record_from_currently_issued_books_table = CurrentlyIssuedBooks.query.filter_by(user_id = this_user.username,
                                                                                        book_id = this_book.book_id).first()
        this_book.issued_copies = this_book.issued_copies - 1        
        this_book.sold_copies = this_book.sold_copies + 1        
        db.session.add(bought_book)
        # Updating UserBookHistory table record
        update_history = UserBookHistory.query.order_by(UserBookHistory.date_issued.desc()).first()
        update_history.date_bought = datetime.now()
        update_history.is_bought = True
        db.session.delete(record_from_currently_issued_books_table)
        db.session.commit()
        return redirect(f"/user_dashboard/{this_user.username}")
    
    return render_template("payment_page.html",username = this_user.username,book_id = this_book.book_id, book_price = this_book.book_price)

# Download book as pdf ----------------------------------------------------------------------------------------------------
@app.route("/download_book/<user_id>/<book_id>")
def download_book(user_id, book_id):
    this_user = LoginCredentials.query.get(user_id)
    this_book = Books.query.get(book_id)

    # Generate pdf file
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size = 12)
    # Add content to PDF
    content = this_book.content
    lines = content.split('\n')
    for line in lines:
        while len(line) > 95:
            pdf.cell(200, 10, txt=line[:95], ln=True)
            line = line[95:]
        pdf.cell(200, 10, txt=line, ln=True)

    # Save the PDF to a file
    file_path = f"static/{this_book.book_id}.pdf"
    pdf.output(file_path)
    
    return send_file(file_path, as_attachment=True)


# User search result -------------------------------------------------------------------------------------------------------------
@app.route("/user_search_result/<user_id>", methods = ["GET", "POST"])
def user_search_result(user_id):
    this_user = LoginCredentials.query.get(user_id)
    if request.method == "POST":
        book_list = Books.query.all()
        user_search_keyword = request.form.get("search-bar-area")
        keyword = user_search_keyword.lower()
        result_list = []
        for book in book_list:
            complete_string = book.book_name + book.authors + book.section.section_name
            complete_string_list = complete_string.split()
            complete_string_without_spaces = ""
            for element in complete_string_list:
                complete_string_without_spaces = complete_string_without_spaces + element
            final_search_string = complete_string_without_spaces.lower()
            if keyword in final_search_string:
                result_list.append((book.book_id, book.book_name, book.section.section_name, book.authors, book.available_copies, book.section_id))
        
        return render_template("user_search_result.html", result_list = result_list, username = this_user.username)


# User Stats ------------------------------------------------------------------------------------------------------------------------
@app.route("/user_stats/<user_id>")
def user_stats(user_id):
    this_user = LoginCredentials.query.get(user_id)
    history = UserBookHistory.query.filter(UserBookHistory.user_id == this_user.username).all()
    if history:
        sections = []
        for record in history:
            book = Books.query.get(record.book_id)
            if book:
                sections.append(book.section.section_name)
            else:
                sections.append("Others")

        plt.clf()
        plt.hist(sections, bins = len(sections))
        plt.xlabel("Section Names----------------------->")
        plt.title("Read Books")
        plt.savefig("static/usg.png")

        return render_template("user_stats.html",username = this_user.username)
    else:
        return "No Stats available"