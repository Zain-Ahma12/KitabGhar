from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from auth import verify_api_key
from database import get_session
from models.users import (
    User,
    UserCreate,
    UserRead,
    UserUpdate,
    apply_user_update,
    user_from_create,
    user_to_read,
)

router = APIRouter(prefix="/user", tags=["Users"])


# helper functions to get users
def get_user_or_404(session: Session, user_id: UUID) -> User:
    """Return the user with this id, or raise a 404 error."""
    user = session.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return user

# helper function to check if an email is already in use
def email_in_use(
    session: Session,
    email: str,
    exclude_id: UUID | None = None,
) -> bool:
    """Check if another user already has this email."""
    query = select(User).where(User.email == email)

    # When updating, the user's own email should not count as a clash.
    if exclude_id is not None:
        query = query.where(User.id != exclude_id)

    return session.exec(query).first() is not None


# API routes
@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    data: UserCreate,
    session: Session = Depends(get_session),
    api_key: str = Depends(verify_api_key),  # requires x-api-key header
):
    """Register a new user."""

    if email_in_use(session, data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    # Convert the request into a database model and save it.
    user = user_from_create(data)
    session.add(user)
    session.commit()
    session.refresh(user)

    return user_to_read(user)


@router.get("/all", response_model=list[UserRead])
def list_users(session: Session = Depends(get_session)):
    """List all users."""
    users = session.exec(select(User)).all()
    return [user_to_read(user) for user in users]


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: UUID,
    session: Session = Depends(get_session),
):
    """Return a single user by id."""
    user = get_user_or_404(session, user_id)
    return user_to_read(user)


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: UUID,
    data: UserUpdate,
    session: Session = Depends(get_session),
):
    """Update only the fields that were sent."""
    user = get_user_or_404(session, user_id)

    # Do not allow two users to share the same email.
    if data.email is not None and email_in_use(
        session, data.email, exclude_id=user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    # apply_user_update raises ValueError for invalid values (e.g. null email).
    try:
        apply_user_update(user, data)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    session.add(user)
    session.commit()
    session.refresh(user)

    return user_to_read(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: UUID,
    session: Session = Depends(get_session),
    api_key: str = Depends(verify_api_key),  # requires x-api-key header
):
    """Delete a user."""
    user = get_user_or_404(session, user_id)

    # A user who still holds books cannot be deleted.
    if user.books:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user still has borrowed books. Return them first.",
        )

    session.delete(user)
    session.commit()