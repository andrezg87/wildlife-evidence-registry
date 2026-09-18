from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.presentation.security import CurrentUser, get_current_user
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest):
    token = await auth_service.authenticate(payload.username, payload.password)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    return LoginResponse(access_token=token)


class CurrentUserOut(BaseModel):
    user_id: str
    role: str


@router.get("/me", response_model=CurrentUserOut)
def get_me(current_user: CurrentUser = Depends(get_current_user)):
    return CurrentUserOut(user_id=current_user.user_id, role=current_user.role)
