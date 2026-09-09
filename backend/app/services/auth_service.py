from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user_schema import UserCreate, UserLogin, UserUpdate
from app.repositories.user_repository import (
    create_user,
    get_user_by_email,
    update_user,
    delete_user
)
from app.auth.security import (
    hash_password,
    verify_password
)
from app.auth.jwt_handler import create_access_token


def register_user(db: Session, user: UserCreate):
    existing_user = get_user_by_email(db, user.email)
    if existing_user:
        return None

    role_val = user.role.value if hasattr(user.role, "value") else str(user.role)

    new_user = User(
        full_name=user.full_name,
        email=user.email,
        password=hash_password(user.password),
        role=role_val
    )

    return create_user(db, new_user)


def login_user(db: Session, user: UserLogin):
    db_user = get_user_by_email(db, user.email)
    if not db_user or not db_user.is_active:
        return None

    if not verify_password(user.password, db_user.password):
        return None

    token = create_access_token(
        {
            "sub": db_user.email,
            "role": db_user.role
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


def get_user_profile(user: User):
    return user


def update_user_profile(db: Session, current_user: User, profile_data: UserUpdate):
    update_dict = {}

    if profile_data.full_name is not None:
        update_dict["full_name"] = profile_data.full_name

    if profile_data.email is not None and profile_data.email != current_user.email:
        existing = get_user_by_email(db, profile_data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address is already in use by another account"
            )
        update_dict["email"] = profile_data.email

    if profile_data.password is not None and profile_data.password.strip():
        update_dict["password"] = hash_password(profile_data.password)

    if profile_data.role is not None:
        role_val = profile_data.role.value if hasattr(profile_data.role, "value") else str(profile_data.role)
        update_dict["role"] = role_val

    return update_user(db, current_user, update_dict)


def delete_user_profile(db: Session, current_user: User):
    return delete_user(db, current_user)
