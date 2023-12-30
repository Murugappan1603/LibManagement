from datetime import date
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import psycopg2

db_params = {
    'host': 'localhost',
    'dbname': 'homework2',
    'user': 'postgres',
    'password': 'Anandh1603'
}

class LibraryManagementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Library Management System")
        self.root.option_add("*Font", "TimesNewRoman 10")
        self.root.option_add("*TButton*font", "TimesNewRoman 10")
        self.student_id_var = tk.StringVar()
        self.borrower_details = None
        self.history_details = None
        self.selected_book_id = tk.StringVar()
        self.create_widgets()

    def fetch_student_details(self):
        entered_student_id = self.student_id_var.get()

        try:
            connection = psycopg2.connect(**db_params)
            cursor = connection.cursor()

            cursor.execute("SELECT student_id, first_name, last_name, email, address, city, state, phone FROM borrower WHERE student_id = %s", (entered_student_id,))
            self.borrower_details = cursor.fetchone()

            if self.borrower_details:
                result_label_text = f"Student ID: {self.borrower_details[0]}\nFirst Name: {self.borrower_details[1]}\nLast Name: {self.borrower_details[2]}\nEmail: {self.borrower_details[3]}\nAddress: {self.borrower_details[4]}\nCity: {self.borrower_details[5]}\nState: {self.borrower_details[6]}\nPhone: {self.borrower_details[7]}"

                borrow_button = ttk.Button(self.root, text="Borrow Book", command=self.borrow_selected_book)
                return_button = ttk.Button(self.root, text="Return Book", command=self.return_book)
                borrowed_books_button = ttk.Button(self.root, text="Books Borrowed", command=self.show_borrowed_books)

                result_label = ttk.Label(self.root, text=result_label_text)
                result_label.grid(row=2, column=0, columnspan=2, pady=10)
                borrow_button.grid(row=3, column=0, padx=10, pady=10)
                return_button.grid(row=3, column=1, padx=10, pady=10)
                borrowed_books_button.grid(row=4, column=0, columnspan=2, pady=10)

            else:
                messagebox.showerror("Error", f"No student found with Student ID: {entered_student_id}")
                self.result_label.config(text="")

        finally:
            cursor.close()
            connection.close()

    def fetch_book_details(self, book_id):
        try:
            connection = psycopg2.connect(**db_params)
            cursor = connection.cursor()

            cursor.execute("SELECT title, author, cover, publisher, pages FROM books WHERE book_id = %s", (book_id,))
            book_details = cursor.fetchone()

            if book_details:
                book_details_text = f"Title: {book_details[0]}\nAuthor: {book_details[1]}\nCover: {book_details[2]}\nPublisher: {book_details[3]}\nPages: {book_details[4]}"
                messagebox.showinfo("Book Details", book_details_text)

            else:
                messagebox.showerror("Error", f"No book found with Book ID: {book_id}")
        finally:
            cursor.close()
            connection.close()

    def handle_membership(self):
        student_id = simpledialog.askinteger("Membership", "Enter Student ID:")
        name = simpledialog.askstring("Membership", "Enter Your Name:")
        timeline = simpledialog.askstring("Membership", "Enter Membership Timeline (e.g., 1 month):")

        if student_id and name and timeline:
            try:
                connection = psycopg2.connect(**db_params)
                cursor = connection.cursor()

                # Check if the student ID already exists in the membership table
                cursor.execute("SELECT 1 FROM membership WHERE student_id = %s", (student_id,))
                member_exists = cursor.fetchone()

                if member_exists:
                    messagebox.showinfo("Membership", "Student is already a member.")
                else:
                    # Check if the student ID already exists in the borrower table
                    cursor.execute("SELECT 1 FROM borrower WHERE student_id = %s", (student_id,))
                    student_exists = cursor.fetchone()

                    if student_exists:
                        # Update existing entry in the borrower table
                        cursor.execute('''
                            UPDATE borrower
                            SET first_name = %s, last_name = %s
                            WHERE student_id = %s
                        ''', (name.split()[0], name.split()[-1], student_id))
                    else:
                        # Add to borrower table
                        cursor.execute('''
                            INSERT INTO borrower (student_id, first_name, last_name, date_joined)
                            VALUES (%s, %s, %s, %s)
                        ''', (student_id, name.split()[0], name.split()[-1], date.today()))

                    # Add to membership table
                    cursor.execute('''
                        INSERT INTO membership (student_id, name, timeline, date)
                        VALUES (%s, %s, %s, %s)
                    ''', (student_id, name, timeline, date.today()))

                    connection.commit()
                    messagebox.showinfo("Membership", "Membership created successfully!")

            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while handling membership: {str(e)}")

            finally:
                cursor.close()
                connection.close()

    def show_available_books(self):
        try:
            connection = psycopg2.connect(**db_params)
            cursor = connection.cursor()

            cursor.execute("SELECT book_id, title, author, cover, publisher, pages FROM books WHERE book_id NOT IN (SELECT book_id FROM history WHERE student_id = %s)", (self.borrower_details[0],))
            available_books = cursor.fetchall()

            available_books_text = "Available Books:\n"
            if available_books:
                for book in available_books:
                    available_books_text += f"Book ID: {book[0]}, Title: {book[1]}, Author: {book[2]}, Cover: {book[3]}, Publisher: {book[4]}, Pages: {book[5]}\n"
            else:
                available_books_text += "No available books at the moment."

            messagebox.showinfo("Available Books", available_books_text)
        finally:
            cursor.close()
            connection.close()

    def borrow_selected_book(self):
        selected_book_id = simpledialog.askinteger("Borrow Book", "Enter Book ID to borrow:")
        if selected_book_id is not None:
            self.selected_book_id.set(selected_book_id)
            self.fetch_book_details(selected_book_id)
            confirm_borrow = messagebox.askyesno("Confirm Borrow", f"Do you want to borrow the book with Book ID {selected_book_id}?")
            if confirm_borrow:
                self.log_borrowed_book(selected_book_id)

    def log_borrowed_book(self, selected_book_id):
        try:
            connection = psycopg2.connect(**db_params)
            cursor = connection.cursor()

            # Check if the student has a membership
            cursor.execute("SELECT 1 FROM membership WHERE student_id = %s", (self.borrower_details[0],))
            has_membership = cursor.fetchone()

            # Set the maximum allowed books based on membership status
            max_allowed_books = 10 if has_membership else 5

            # Check if the student has already borrowed the maximum number of books
            cursor.execute("SELECT COUNT(*) FROM history WHERE student_id = %s", (self.borrower_details[0],))
            books_borrowed_count = cursor.fetchone()[0]

            if books_borrowed_count >= max_allowed_books:
                messagebox.showerror("Error",
                                     f"You have reached the maximum number of books allowed ({max_allowed_books}).")
                return

            cursor.execute("SELECT student_id FROM history WHERE book_id = %s", (selected_book_id,))
            already_borrowed = cursor.fetchone()

            if already_borrowed:
                messagebox.showerror("Error",
                                     f"The book with Book ID {selected_book_id} is already borrowed by another student.")
                return

            cursor.execute("SELECT title, author, cover, publisher, pages FROM books WHERE book_id = %s",
                           (selected_book_id,))
            book_details = cursor.fetchone()

            if book_details:
                cursor.execute("SELECT COALESCE(MAX(transaction_id), 0) FROM history")
                max_transaction_id = cursor.fetchone()[0] + 1

                cursor.execute('''
                    INSERT INTO history (transaction_id, student_id, book_id) 
                    VALUES (%s, %s, %s)
                ''', (max_transaction_id, self.borrower_details[0], selected_book_id))

                connection.commit()

                cursor.execute("SELECT transaction_id, book_id FROM history WHERE student_id = %s",
                               (self.borrower_details[0],))
                self.history_details = cursor.fetchall()

                updated_result_label_text = f"Student ID: {self.borrower_details[0]}\nFirst Name: {self.borrower_details[1]}\nLast Name: {self.borrower_details[2]}\nEmail: {self.borrower_details[3]}\nAddress: {self.borrower_details[4]}\nCity: {self.borrower_details[5]}\nState: {self.borrower_details[6]}\nPhone: {self.borrower_details[7]}"
                self.result_label.config(text=updated_result_label_text)

                messagebox.showinfo("Borrow Book",
                                    f"The book with Book ID {selected_book_id} has been successfully borrowed!")

            else:
                messagebox.showerror("Error", f"No book found with Book ID: {selected_book_id}")

        finally:
            cursor.close()
            connection.close()

    def show_borrowed_books(self):
        if not self.borrower_details:
            messagebox.showinfo("Borrowed Books", "No student details available.")
            return

        try:
            connection = psycopg2.connect(**db_params)
            cursor = connection.cursor()

            cursor.execute("SELECT h.transaction_id, h.book_id, b.title FROM history h JOIN books b ON h.book_id = b.book_id WHERE h.student_id = %s", (self.borrower_details[0],))
            borrowed_books = cursor.fetchall()

            borrowed_books_text = "\nBooks Borrowed by the Student:"
            if borrowed_books:
                for history_row in borrowed_books:
                    borrowed_books_text += f"\nTransaction ID: {history_row[0]}, Book ID: {history_row[1]}, Title: {history_row[2]}"

                messagebox.showinfo("Borrowed Books", borrowed_books_text)
            else:
                messagebox.showinfo("Borrowed Books", "No books borrowed by the student.")

        finally:
            cursor.close()
            connection.close()

    def return_book(self):
        if not self.borrower_details:
            messagebox.showinfo("Return Book", "No student details available.")
            return

        selected_book_id = simpledialog.askinteger("Return Book", "Enter Book ID to return:")
        if selected_book_id is not None:
            self.return_book_db(selected_book_id)

    def return_book_db(self, selected_book_id):
        try:
            connection = psycopg2.connect(**db_params)
            cursor = connection.cursor()

            # Check if the student has borrowed the specified book
            cursor.execute("SELECT 1 FROM history WHERE student_id = %s AND book_id = %s", (self.borrower_details[0], selected_book_id))
            is_borrowed = cursor.fetchone()

            if not is_borrowed:
                messagebox.showerror("Error", f"You have not borrowed the book with Book ID: {selected_book_id}")
                return

            # Fetch book details
            cursor.execute("SELECT title, author, cover, publisher, pages FROM books WHERE book_id = %s", (selected_book_id,))
            book_details = cursor.fetchone()

            if book_details:
                book_details_text = f"Title: {book_details[0]}\nAuthor: {book_details[1]}\nCover: {book_details[2]}\nPublisher: {book_details[3]}\nPages: {book_details[4]}"

                # Confirm return
                confirm_return = messagebox.askyesno("Confirm Return", f"Do you want to return the following book?\n\n{book_details_text}")
                if confirm_return:
                    # Delete book from history
                    cursor.execute("DELETE FROM history WHERE student_id = %s AND book_id = %s", (self.borrower_details[0], selected_book_id))
                    connection.commit()

                    # Refresh the history details after returning the book
                    cursor.execute("SELECT transaction_id, book_id FROM history WHERE student_id = %s", (self.borrower_details[0],))
                    self.history_details = cursor.fetchall()

                    # Check if the book is still in history after returning
                    cursor.execute("SELECT 1 FROM history WHERE student_id = %s AND book_id = %s", (self.borrower_details[0], selected_book_id))
                    is_still_borrowed = cursor.fetchone()

                    if not is_still_borrowed:
                        # Update the displayed label
                        updated_result_label_text = f"Student ID: {self.borrower_details[0]}\nFirst Name: {self.borrower_details[1]}\nLast Name: {self.borrower_details[2]}\nEmail: {self.borrower_details[3]}\nAddress: {self.borrower_details[4]}\nCity: {self.borrower_details[5]}\nState: {self.borrower_details[6]}\nPhone: {self.borrower_details[7]}\n\nHistory Details:"
                        if self.history_details:
                            for history_row in self.history_details:
                                updated_result_label_text += f"\nTransaction ID: {history_row[0]}, Book ID: {history_row[1]}"

                        self.result_label.config(text=updated_result_label_text)

                        messagebox.showinfo("Return Book", f"The book with Book ID {selected_book_id} has been successfully returned and removed from history!")

                    else:
                        messagebox.showerror("Error", f"An error occurred while returning the book with Book ID {selected_book_id}")

            else:
                messagebox.showerror("Error", f"No book found with Book ID: {selected_book_id}")

        finally:
            cursor.close()
            connection.close()

    def add_author(self):
        author_id = simpledialog.askinteger("Add Author", "Enter Author ID:")
        if author_id is not None:
            author_name = simpledialog.askstring("Add Author", "Enter Author Name:")
            book_id = simpledialog.askinteger("Add Author", "Enter Book ID:")
            genre = simpledialog.askstring("Add Author", "Enter Genre:")
            title = simpledialog.askstring("Add Author", "Enter Title:")

            try:
                connection = psycopg2.connect(**db_params)
                cursor = connection.cursor()

                # Check if the book already exists in the books table
                cursor.execute("SELECT 1 FROM books WHERE book_id = %s", (book_id,))
                book_exists = cursor.fetchone()

                if not book_exists:
                    # If the book doesn't exist, add it to the books table
                    cursor.execute('''
                        INSERT INTO books (book_id, title)
                        VALUES (%s, %s)
                    ''', (book_id, title))

                # Add the author to the author table
                cursor.execute('''
                    INSERT INTO author (author_id, author_name, book_id, genre, title)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (author_id, author_name, book_id, genre, title))

                connection.commit()
                messagebox.showinfo("Add Author", f"Author added successfully!\nAuthor ID: {author_id}")

            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while adding author: {str(e)}")

            finally:
                cursor.close()
                connection.close()

    def add_genre(self):
        genre_id = simpledialog.askinteger("Add Genre", "Enter Genre ID:")
        if genre_id is not None:
            genre = simpledialog.askstring("Add Genre", "Enter Genre Name:")
            book_id = simpledialog.askinteger("Add Genre", "Enter Book ID:")

            try:
                connection = psycopg2.connect(**db_params)
                cursor = connection.cursor()

                # Check if the book already exists in the books table
                cursor.execute("SELECT 1 FROM books WHERE book_id = %s", (book_id,))
                book_exists = cursor.fetchone()

                if not book_exists:
                    # If the book doesn't exist, add it to the books table
                    cursor.execute('''
                        INSERT INTO books (book_id)
                        VALUES (%s)
                    ''', (book_id,))

                # Add the genre to the genre table
                cursor.execute('''
                    INSERT INTO genre (genre_id, genre, book_id)
                    VALUES (%s, %s, %s)
                ''', (genre_id, genre, book_id))

                connection.commit()
                messagebox.showinfo("Add Genre", f"Genre added successfully!\nGenre ID: {genre_id}")

            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while adding genre: {str(e)}")

            finally:
                cursor.close()
                connection.close()

    def create_widgets(self):
        student_id_label = ttk.Label(self.root, text="Enter Student ID:")
        self.student_id_entry = ttk.Entry(self.root, textvariable=self.student_id_var)
        fetch_details_button = ttk.Button(self.root, text="Fetch Student", command=self.fetch_student_details)

        student_id_label.grid(row=0, column=0, padx=15, pady=5, sticky="w")
        self.student_id_entry.grid(row=0, column=1, padx=15, pady=5, sticky="w")
        fetch_details_button.grid(row=1, column=0, columnspan=2, pady=10)

        self.result_label = ttk.Label(self.root, text="")
        self.result_label.grid(row=2, column=0, columnspan=2, pady=10)

        add_author_button = ttk.Button(self.root, text="Add Author", command=self.add_author)
        add_author_button.grid(row=5, column=0, columnspan=2, pady=10)
        add_genre_button = ttk.Button(self.root, text="Add Genre", command=self.add_genre)
        add_genre_button.grid(row=6, column=0, columnspan=2, pady=10)
        membership_button = ttk.Button(self.root, text="Membership", command=self.handle_membership)
        membership_button.grid(row=7, column=0, columnspan=2, pady=10)
        quit_button = ttk.Button(self.root, text="Quit", command=self.root.destroy)
        quit_button.grid(row=8, column=0, columnspan=2, pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = LibraryManagementApp(root)
    root.mainloop()
