from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

app = FastAPI(title="Library API", version="1.0.0")

class Book(BaseModel):
    id: Optional[int] = None
    title: str
    author: str
    published_year: int
    is_available: bool = True

class BookCreate(BaseModel):
    title: str
    author: str
    published_year: int

# In-memory database
books_db = {}
current_id = 1

@app.post("/books/", response_model=Book)
async def create_book(book: BookCreate):
    global current_id
    new_book = Book(
        id=current_id,
        title=book.title,
        author=book.author,
        published_year=book.published_year,
        is_available=True
    )
    books_db[current_id] = new_book
    current_id += 1
    return new_book

@app.get("/books/", response_model=List[Book])
async def list_books():
    return list(books_db.values())

@app.get("/books/{book_id}", response_model=Book)
async def get_book(book_id: int):
    if book_id not in books_db:
        raise HTTPException(status_code=404, detail="Book not found")
    return books_db[book_id]

@app.put("/books/{book_id}/borrow")
async def borrow_book(book_id: int):
    if book_id not in books_db:
        raise HTTPException(status_code=404, detail="Book not found")
    
    book = books_db[book_id]
    if not book.is_available:
        raise HTTPException(status_code=400, detail="Book is already borrowed")
    
    book.is_available = False
    return {"message": "Book borrowed successfully"}

@app.put("/books/{book_id}/return")
async def return_book(book_id: int):
    if book_id not in books_db:
        raise HTTPException(status_code=404, detail="Book not found")
    
    book = books_db[book_id]
    if book.is_available:
        raise HTTPException(status_code=400, detail="Book is not borrowed")
    
    book.is_available = True
    return {"message": "Book returned successfully"}
