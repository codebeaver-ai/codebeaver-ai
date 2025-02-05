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
