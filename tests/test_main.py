from fastapi.testclient import TestClient
import pytest
from app.main import app





client = TestClient(app)


def test_create_and_get_book():
    # Test creating a new book
    book_data = {
        "title": "The Great Gatsby",
        "author": "F. Scott Fitzgerald",
        "published_year": 1925,
    }
    response = client.post("/books/", json=book_data)
    assert response.status_code == 200
    created_book = response.json()
    assert created_book["title"] == book_data["title"]
    assert created_book["author"] == book_data["author"]
    assert created_book["published_year"] == book_data["published_year"]
    assert created_book["is_available"] == True

    # Test getting the created book
    book_id = created_book["id"]
    response = client.get(f"/books/{book_id}")
    assert response.status_code == 200
    retrieved_book = response.json()
    assert retrieved_book == created_book


def test_list_books():
    # Create a book first
    book_data = {"title": "1984", "author": "George Orwell", "published_year": 1949}
    client.post("/books/", json=book_data)

    # Test listing all books
    response = client.get("/books/")
    assert response.status_code == 200
    books = response.json()
    assert len(books) > 0
    assert isinstance(books, list)


def test_borrow_and_return_book():
    """
    Test the book borrowing and returning functionality.
    This test covers:
    1. Creating a new book
    2. Borrowing the book
    3. Attempting to borrow an already borrowed book
    4. Returning the book
    5. Attempting to return an available book
    """
    # Create a new book
    book_data = {
        "title": "To Kill a Mockingbird",
        "author": "Harper Lee",
        "published_year": 1960,
    }
    response = client.post("/books/", json=book_data)
    assert response.status_code == 200
    created_book = response.json()
    book_id = created_book["id"]

    # Borrow the book
    response = client.put(f"/books/{book_id}/borrow")
    assert response.status_code == 200
    assert response.json() == {"message": "Book borrowed successfully"}

    # Try to borrow the same book again (should fail)
    response = client.put(f"/books/{book_id}/borrow")
    assert response.status_code == 400
    assert response.json() == {"detail": "Book is already borrowed"}

    # Return the book
    response = client.put(f"/books/{book_id}/return")
    assert response.status_code == 200
    assert response.json() == {"message": "Book returned successfully"}

    # Try to return the book again (should fail)
    response = client.put(f"/books/{book_id}/return")
    assert response.status_code == 400
    assert response.json() == {"detail": "Book is not borrowed"}
