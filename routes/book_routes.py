from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import selectinload
from sqlmodel import Session, SQLModel, col, func, select

from auth import verify_api_key
from database import get_session
from models.books import (
    Book,
    BookBorrowRequest,
    BookCreate,
    BookRead,
    BookUpdate,
    book_to_read,
    borrow_book,
    return_book,
    utc_now,
    validate_book_state,
)

router = APIRouter(prefix="/book", tags=["Books"])



class BookPage(SQLModel):
    """One page of books plus pagination info."""

    total: int  # how many books match in total
    page: int
    page_size: int
    items: list[BookRead]


class BorrowedBookItem(SQLModel):
    """Short info about one borrowed book."""

    book_id: int
    book_name: str
    book_author: str
    borrow_start_date: date | None
    borrow_end_date: date | None


class BorrowerInfo(SQLModel):
    """A borrower and every book they currently hold."""

    borrower_id: UUID
    borrower_name: str | None  # first name + last name
    books: list[BorrowedBookItem]


# helper functions for routes
def get_book_or_404(session: Session, book_id: int) -> Book:
    """Return the book with this id, or raise a 404 error."""
    book = session.get(Book, book_id)

    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found.",
        )

    return book


def paginate(
    session: Session,
    query,
    page: int,
    page_size: int,
) -> BookPage:
    """Run a book query and return only the requested page."""

    # Count all matching rows (before applying the page limits).
    total = session.exec(
        select(func.count()).select_from(query.subquery())
    ).one()

    # Fetch only this page. selectinload loads the borrowers in one extra
    # query instead of one query per book.
    books = session.exec(
        query.options(selectinload(Book.borrower))
        .order_by(Book.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return BookPage(
        total=total,
        page=page,
        page_size=page_size,
        items=[book_to_read(book) for book in books],
    )



@router.post(
    "/new",
    response_model=BookRead,
    status_code=status.HTTP_201_CREATED,
)
def add_book(
    data: BookCreate,
    session: Session = Depends(get_session),
    api_key: str = Depends(verify_api_key),  # requires x-api-key header
):
    """Add a new book. New books start as available."""

    book = Book(**data.model_dump())

    validate_book_state(book)

    session.add(book)
    session.commit()
    session.refresh(book)

    return book_to_read(book)


@router.get("/all", response_model=BookPage)
def get_all_books(
    book_name: str | None = Query(default=None, description="Partial match"),
    author: str | None = Query(default=None, description="Partial match"),
    publish_year: int | None = Query(default=None, ge=1000, le=9999),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    session: Session = Depends(get_session),
):
    """Get all books. Optional filters: book_name, author, publish_year."""

    query = select(Book)

    # Add a filter only when the client sent that query parameter.
    if book_name:
        query = query.where(col(Book.book_name).ilike(f"%{book_name}%"))
    if author:
        query = query.where(col(Book.author).ilike(f"%{author}%"))
    if publish_year is not None:
        query = query.where(Book.published_year == publish_year)

    return paginate(session, query, page, page_size)


@router.get("/available", response_model=BookPage)
def get_available_books(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    session: Session = Depends(get_session),
):
    """Get all books that can be borrowed right now."""

    query = select(Book).where(col(Book.is_available).is_(True))

    return paginate(session, query, page, page_size)


@router.get("/borrowed", response_model=BookPage)
def get_borrowed_books(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    session: Session = Depends(get_session),
):
    """
    Get all borrowed books.
    Each book includes borrower_id, borrower_name and the borrow dates.
    """

    query = select(Book).where(col(Book.is_borrowed).is_(True))

    return paginate(session, query, page, page_size)


@router.get("/borrowers_info", response_model=list[BorrowerInfo])
def get_borrowers_info(session: Session = Depends(get_session)):
    """Group the borrowed books by borrower."""

    borrowed_books = session.exec(
        select(Book)
        .where(col(Book.is_borrowed).is_(True))
        .options(selectinload(Book.borrower))
        .order_by(Book.id)
    ).all()

    # Key = borrower id, value = that borrower's info.
    borrowers: dict[UUID, BorrowerInfo] = {}

    for book in borrowed_books:
        # First time we see this borrower: create their entry.
        if book.borrower_id not in borrowers:
            borrowers[book.borrower_id] = BorrowerInfo(
                borrower_id=book.borrower_id,
                borrower_name=book.borrower_name,
                books=[],
            )

        # Add this book to the borrower's list.
        borrowers[book.borrower_id].books.append(
            BorrowedBookItem(
                book_id=book.id,
                book_name=book.book_name,
                book_author=book.author,
                borrow_start_date=book.borrow_start_date,
                borrow_end_date=book.borrow_end_date,
            )
        )

    return list(borrowers.values())


@router.get("/{book_id}", response_model=BookRead)
def get_book(
    book_id: int,
    session: Session = Depends(get_session),
):
    """Get a single book by id."""
    book = get_book_or_404(session, book_id)
    return book_to_read(book)


@router.patch("/{book_id}", response_model=BookRead)
def update_book(
    book_id: int,
    data: BookUpdate,
    session: Session = Depends(get_session),
):
    """
    Update book_name, author, published_year, condition,
    is_available and is_borrowed. Only the fields sent are changed.
    """
    book = get_book_or_404(session, book_id)

    # Copy only the fields the client actually sent onto the book.
    changes = data.model_dump(exclude_unset=True)
    for field_name, value in changes.items():
        setattr(book, field_name, value)

    # A book that is available again must not keep old borrower/removal info.
    if book.is_available:
        book.borrower = None
        book.borrower_id = None
        book.borrow_start_date = None
        book.borrow_end_date = None
        book.removed_date = None

    book.updated_at = utc_now()

    # Make sure the final combination of fields is a valid book state.
    try:
        validate_book_state(book)
    except ValueError as error:
        session.rollback()  # throw away the unsaved changes
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    session.add(book)
    session.commit()
    session.refresh(book)

    return book_to_read(book)


@router.post("/{book_id}/borrow", response_model=BookRead)
def borrow_a_book(
    book_id: int,
    data: BookBorrowRequest,
    session: Session = Depends(get_session),
):
    """Borrow a book for an existing user."""
    book = get_book_or_404(session, book_id)

    # borrow_book checks that the book is free and the user exists.
    try:
        return borrow_book(session, book, data)
    except ValueError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@router.post("/{book_id}/return", response_model=BookRead)
def return_a_book(
    book_id: int,
    session: Session = Depends(get_session),
):
    """Return a borrowed book so it becomes available again."""
    book = get_book_or_404(session, book_id)

    try:
        return return_book(session, book)
    except ValueError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )