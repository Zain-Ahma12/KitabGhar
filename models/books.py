from datetime import date
from enum import Enum
from uuid import UUID

from pydantic import model_validator
from sqlmodel import Field, Relationship, Session, SQLModel
from datetime import date, datetime, timezone
from typing import Optional

def utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


class BookCondition(str, Enum):
    """Allowed physical conditions of a book."""

    NEW = "new"
    GOOD = "good"
    OK = "ok"
    BAD = "bad"
    REMOVED = "removed"


# book table
class Book(SQLModel, table=True):

    id: int | None = Field(default=None, primary_key=True)

    book_name: str = Field(index=True, max_length=200)
    author: str = Field(index=True, max_length=150)

    published_year: int = Field(ge=1000, le=9999)

    # A new book is available by default.
    is_available: bool = Field(default=True)
    is_borrowed: bool = Field(default=False)

    condition: BookCondition = Field(default=BookCondition.NEW)

    # Required when a book is removed.
    removed_date: date | None = None

    # Foreign key referencing users.id.
    borrower_id: UUID | None = Field(
        default=None,
        foreign_key="user.id",
        index=True,
    )

    # Store the beginning and end of the borrowing period.
    borrow_start_date: date | None = None
    borrow_end_date: date | None = None

    # Many books can belong to the same borrower.
    borrower: Optional["User"] = Relationship(
        back_populates="books"
    )

    @property
    def borrower_name(self) -> str | None:
        """Get the borrower's full name from the User model."""

        if self.borrower is None:
            return None

        return (
            f"{self.borrower.firstname} "
            f"{self.borrower.lastname}"
        ).strip()


class BookCreate(SQLModel):
    """Request body for adding a new book."""

    book_name: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=150)
    published_year: int = Field(ge=1000, le=9999)

    condition: BookCondition = BookCondition.NEW

    @model_validator(mode="after")
    def validate_condition(self):
        """New books must enter through the normal workflow."""

        if self.condition == BookCondition.REMOVED:
            raise ValueError(
                "Use the removal operation to remove a book."
            )

        return self


class BookUpdate(SQLModel):
    """Request body for partially updating book details."""

    book_name: str | None = Field(
        default=None, min_length=1, max_length=200
    )
    author: str | None = Field(
        default=None, min_length=1, max_length=150
    )
    published_year: int | None = Field(
        default=None, ge=1000, le=9999
    )
    condition: BookCondition | None = None

    @model_validator(mode="after")
    def validate_update(self):
        """Reject empty updates and invalid nullable values."""

        if not self.model_fields_set:
            raise ValueError(
                "Provide at least one field to update."
            )

        for field_name in (
            "book_name",
            "author",
            "published_year",
            "condition",
        ):
            if (
                field_name in self.model_fields_set
                and getattr(self, field_name) is None
            ):
                raise ValueError(
                    f"{field_name} cannot be null."
                )

        if self.condition == BookCondition.REMOVED:
            raise ValueError(
                "Use the removal operation to remove a book."
            )

        return self


class BookBorrowRequest(SQLModel):
    """Request body for borrowing a book."""

    borrower_id: UUID
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_dates(self):
        """Ensure that the end date is not before the start date."""

        if self.end_date < self.start_date:
            raise ValueError(
                "end_date must not be earlier than start_date."
            )

        return self


class BookRead(SQLModel):
    """Response body returned to the API client."""

    id: int
    book_name: str
    author: str
    published_year: int

    is_available: bool
    is_borrowed: bool
    condition: BookCondition

    removed_date: date | None

    borrower_id: UUID | None
    borrower_name: str | None

    borrow_start_date: date | None
    borrow_end_date: date | None




def book_to_read(book: Book) -> BookRead:
    """Convert a database book into an API response."""

    if book.id is None:
        raise ValueError("Save the book before creating a response.")

    return BookRead(
        id=book.id,
        book_name=book.book_name,
        author=book.author,
        published_year=book.published_year,
        is_available=book.is_available,
        is_borrowed=book.is_borrowed,
        condition=book.condition,
        removed_date=book.removed_date,
        borrower_id=book.borrower_id,
        borrower_name=book.borrower_name,
        borrow_start_date=book.borrow_start_date,
        borrow_end_date=book.borrow_end_date,
    )


def validate_book_state(book: Book) -> None:
    """
    Check that the book is in exactly one valid state.

    Available:
        is_available=True, is_borrowed=False

    Borrowed:
        is_available=False, is_borrowed=True

    Removed:
        is_available=False, is_borrowed=False
        and condition=REMOVED
    """

    if book.is_available and book.is_borrowed:
        raise ValueError(
            "A book cannot be available and borrowed together."
        )

    # STATE 1: AVAILABLE
    if book.is_available:
        if book.condition == BookCondition.REMOVED:
            raise ValueError(
                "A removed book cannot be available."
            )

        if any((
            book.borrower_id is not None,
            book.borrow_start_date is not None,
            book.borrow_end_date is not None,
            book.removed_date is not None,
        )):
            raise ValueError(
                "An available book cannot have borrower details "
                "or a removal date."
            )

        return

    # STATE 2: BORROWED
    if book.is_borrowed:
        if book.condition == BookCondition.REMOVED:
            raise ValueError(
                "A removed book cannot be borrowed."
            )

        if (
            book.borrower_id is None
            or book.borrow_start_date is None
            or book.borrow_end_date is None
        ):
            raise ValueError(
                "A borrowed book requires a borrower and both dates."
            )

        if book.borrow_start_date > book.borrow_end_date:
            raise ValueError(
                "The borrowing start date cannot exceed the end date."
            )

        if book.removed_date is not None:
            raise ValueError(
                "A borrowed book cannot have a removal date."
            )

        return

    # STATE 3: REMOVED
    if book.condition != BookCondition.REMOVED:
        raise ValueError(
            "A book that is neither available nor borrowed "
            "must have condition 'removed'."
        )

    if book.removed_date is None:
        raise ValueError(
            "A removed book must have a removal date."
        )

    if any((
        book.borrower_id is not None,
        book.borrow_start_date is not None,
        book.borrow_end_date is not None,
    )):
        raise ValueError(
            "A removed book cannot have borrower details."
        )

# helper functions for borrowing, returning, and removing books
def borrow_book(
    session: Session,
    book: Book,
    request: BookBorrowRequest,
) -> BookRead:
    """Borrow a book for an existing user."""

    if not book.is_available or book.is_borrowed:
        raise ValueError("This book is not available.")

    if book.condition == BookCondition.REMOVED:
        raise ValueError("This book has been removed.")

    borrower = session.get(User, request.borrower_id)

    if borrower is None:
        raise ValueError("Borrower does not exist.")

    book.is_available = False
    book.is_borrowed = True

    book.borrower = borrower
    book.borrower_id = borrower.id

    book.borrow_start_date = request.start_date
    book.borrow_end_date = request.end_date

    validate_book_state(book)

    session.add(book)
    session.commit()
    session.refresh(book)

    return book_to_read(book)


def return_book(
    session: Session,
    book: Book,
) -> BookRead:
    """Return a borrowed book to the available state."""

    if not book.is_borrowed:
        raise ValueError("This book is not currently borrowed.")

    book.is_available = True
    book.is_borrowed = False

    book.borrower = None
    book.borrower_id = None
    book.borrow_start_date = None
    book.borrow_end_date = None

    validate_book_state(book)

    session.add(book)
    session.commit()
    session.refresh(book)

    return book_to_read(book)


def remove_book(
    session: Session,
    book: Book,
) -> BookRead:
    """Remove an available book from circulation."""

    if book.is_borrowed:
        raise ValueError(
            "Return the book before removing it."
        )

    book.is_available = False
    book.is_borrowed = False
    book.condition = BookCondition.REMOVED
    book.removed_date = date.today()

    book.borrower = None
    book.borrower_id = None
    book.borrow_start_date = None
    book.borrow_end_date = None

    validate_book_state(book)

    session.add(book)
    session.commit()
    session.refresh(book)

    return book_to_read(book)


from models.users import User
Book.model_rebuild()  # Rebuild the model to resolve the forward reference to User