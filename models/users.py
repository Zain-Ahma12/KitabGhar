import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel




def utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)



# User table
class User(SQLModel, table=True):
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    firstname: str = Field(index=True, max_length=100)
    lastname: str = Field(max_length=100)

    email: str = Field(index=True, unique=True, max_length=254)

    # Phone numbers should be strings to preserve
    # country codes, leading zeroes, and '+' signs.
    number: str | None = Field(default=None, max_length=30)

    college: str = Field(max_length=200)

    # Stored as a JSON-encoded string in the database.
    # Example: '["fiction", "mystery"]'
    fav_book_genres: str | None = Field(default=None)

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    # One user can borrow multiple books.
    books: list["Book"] = Relationship(
        back_populates="borrower"
    )


class UserCreate(SQLModel):
    """Request body for creating a user."""

    firstname: str = Field(min_length=1, max_length=100)
    lastname: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=1, max_length=254)
    number: str | None = Field(default=None, max_length=30)
    college: str = Field(min_length=1, max_length=200)

    # The API accepts a normal Python list.
    fav_book_genres: list[str] | None = None


class UserUpdate(SQLModel):
    """Request body for partially updating a user."""

    firstname: str | None = Field(
        default=None, min_length=1, max_length=100
    )
    lastname: str | None = Field(
        default=None, min_length=1, max_length=100
    )
    email: str | None = Field(
        default=None, min_length=1, max_length=254
    )
    number: str | None = Field(default=None, max_length=30)
    college: str | None = Field(
        default=None, min_length=1, max_length=200
    )
    fav_book_genres: list[str] | None = None



class UserRead(SQLModel):
    """Response body returned to the API client."""

    id: UUID
    firstname: str
    lastname: str
    email: str
    number: str | None
    college: str

    # Return a list to the client instead of a JSON string.
    fav_book_genres: list[str] | None

    created_at: datetime
    updated_at: datetime


# Conversion helpers functions
def user_from_create(data: UserCreate) -> User:
    """Convert a user request into a database model."""

    values = data.model_dump()
    genres = values.pop("fav_book_genres")

    # Convert the Python list into a JSON string for storage.
    values["fav_book_genres"] = (
        json.dumps(genres) if genres is not None else None
    )

    return User(**values)


def user_to_read(user: User) -> UserRead:
    """Convert a database user into an API response."""

    genres = (
        json.loads(user.fav_book_genres)
        if user.fav_book_genres is not None
        else None
    )

    return UserRead(
        id=user.id,
        firstname=user.firstname,
        lastname=user.lastname,
        email=user.email,
        number=user.number,
        college=user.college,
        fav_book_genres=genres,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def apply_user_update(user: User, data: UserUpdate) -> User:
    """Apply only the fields provided in an update request."""

    values = data.model_dump(exclude_unset=True)

    if "fav_book_genres" in values:
        genres = values["fav_book_genres"]
        values["fav_book_genres"] = (
            json.dumps(genres) if genres is not None else None
        )

    for field_name, value in values.items():
        if field_name == "email" and value is None:
            raise ValueError("Email cannot be null.")

        if field_name == "firstname" and value is None:
            raise ValueError("Firstname cannot be null.")

        if field_name == "lastname" and value is None:
            raise ValueError("Lastname cannot be null.")

        if field_name == "college" and value is None:
            raise ValueError("College cannot be null.")

        setattr(user, field_name, value)

    # Refresh the timestamp whenever the user is updated.
    user.updated_at = utc_now()

    return user


from models.books import Book
User.model_rebuild()  # Rebuild the model to resolve the forward reference to Book
