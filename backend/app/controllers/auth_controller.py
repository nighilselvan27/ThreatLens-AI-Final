from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.schemas.user_schema import (
    UserCreate,
    UserLogin,
    UserUpdate,
    UserResponse,
    Token,
    UserRole
)
from app.services.auth_service import (
    register_user,
    login_user,
    get_user_profile,
    update_user_profile,
    delete_user_profile
)
from app.middleware.auth_middleware import (
    get_current_user,
    RoleChecker
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# --------------------------------------------------
# REGISTER
# --------------------------------------------------

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    new_user = register_user(db, user)

    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    return new_user


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@router.post(
    "/login",
    response_model=Token
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # OAuth2 uses "username", but our application
    # uses email as the username.
    user = UserLogin(
        email=form_data.username,
        password=form_data.password
    )

    token = login_user(db, user)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    return token


# --------------------------------------------------
# GET PROFILE
# --------------------------------------------------

@router.get(
    "/profile",
    response_model=UserResponse
)
def get_profile(
    current_user: User = Depends(get_current_user)
):
    return get_user_profile(current_user)


# --------------------------------------------------
# UPDATE PROFILE
# --------------------------------------------------

@router.put(
    "/profile",
    response_model=UserResponse
)
def update_profile(
    profile_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return update_user_profile(
        db,
        current_user,
        profile_data
    )


# --------------------------------------------------
# DELETE PROFILE
# --------------------------------------------------

@router.delete("/profile")
def delete_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    delete_user_profile(
        db,
        current_user
    )

    return {
        "message": "User account successfully deleted"
    }


# --------------------------------------------------
# ADMIN DASHBOARD - RBAC EXAMPLE
# --------------------------------------------------

@router.get(
    "/admin/dashboard",
    dependencies=[
        Depends(RoleChecker([UserRole.ADMIN]))
    ]
)
def admin_dashboard(
    current_user: User = Depends(get_current_user)
):
    return {
        "message": (
            f"Welcome Admin {current_user.full_name} "
            "to ThreatLens Admin Dashboard"
        ),
        "system_status": (
            "All malware detection engines operational"
        )
    }