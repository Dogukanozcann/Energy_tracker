from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
    VerifyEmailRequest,
)
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni kullanıcı kaydı",
)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Email + şifre ile yeni hesap oluşturur. Başarılıysa JWT token döner."""
    auth_service = AuthService(db)

    try:
        user = await auth_service.register(data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    token = auth_service.issue_token(user)
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Kullanıcı girişi",
)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Email + şifre ile giriş. JWT token döner."""
    auth_service = AuthService(db)
    user_service = UserService(db)

    try:
        user = await auth_service.authenticate(data.email, data.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    await user_service.update_last_login(user)
    token = auth_service.issue_token(user)

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Giriş yapan kullanıcının bilgisi",
)
async def me(
    current_user: User = Depends(get_current_user),
):
    """Access token ile giriş yapan kullanıcının profilini döner."""
    return UserResponse.model_validate(current_user)


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    summary="E-posta doğrulama",
)
async def verify_email(
    data: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
):
    """Kayıt sonrası e-posta adresini doğrular."""
    auth_service = AuthService(db)
    try:
        await auth_service.verify_email(data.token)
        return MessageResponse(message="E-posta başarıyla doğrulandı.")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Şifre sıfırlama talebi",
)
async def forgot_password(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Email'e şifre sıfırlama bağlantısı gönderir.
    Email kayıtlı değilse bile başarılı döner (güvenlik).
    """
    auth_service = AuthService(db)
    await auth_service.forgot_password(data.email)
    return MessageResponse(
        message="Şifre sıfırlama bağlantısı e-posta adresinize gönderildi."
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Şifre sıfırlama",
)
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Token ile yeni şifre belirler."""
    auth_service = AuthService(db)
    try:
        await auth_service.reset_password(data.token, data.new_password)
        return MessageResponse(message="Şifreniz başarıyla sıfırlandı.")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
