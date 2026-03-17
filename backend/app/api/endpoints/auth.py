from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Any, List

from backend.app.core.database import get_dest_db
from backend.app.models.models import User
from backend.app.schemas.user import UserCreate, UserResponse, Token, ChangePasswordModel
from backend.app.core.security import verify_password, get_password_hash, create_access_token
from backend.app.core.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
def get_users(
    db: Session = Depends(get_dest_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Consulta no permitida")
    return db.query(User).all()

@router.put("/{user_id}/status")
def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_dest_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Operación no permitida")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    user.is_active = not user.is_active
    db.commit()
    return {"message": "Status updated"}

@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_dest_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    # OAuth2 specifies username instead of email, we use username as email here
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return {
        "access_token": create_access_token(user.id),
        "token_type": "bearer"
    }

@router.post("/register", response_model=UserResponse)
def register_user(
    *,
    db: Session = Depends(get_dest_db),
    user_in: UserCreate,
    current_user: User = Depends(get_current_user)
) -> Any:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough privileges to create users")
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role or "operator",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/me", response_model=UserResponse)
def read_user_me(
    current_user: User = Depends(get_current_user)
) -> Any:
    return current_user

@router.put("/me/password")
def change_password(
    obj_in: ChangePasswordModel,
    db: Session = Depends(get_dest_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    if not verify_password(obj_in.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
    
    current_user.hashed_password = get_password_hash(obj_in.new_password)
    db.commit()
    return {"message": "Password updated successfully"}
