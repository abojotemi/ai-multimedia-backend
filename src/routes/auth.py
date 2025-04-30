from fastapi import APIRouter, HTTPException, status, Depends, Response, Cookie, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional
from datetime import datetime, timezone

from src.models.user import User
from src.schemas.auth import (
    LoginRequest, 
    RegisterRequest, 
    TokenResponse, 
    UserResponse,
    RefreshTokenRequest
)
from src.utils.auth import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token,
    get_current_user,
    get_current_user_from_refresh_token,
    blacklist_token,
    decode_token,
    TOKEN_TYPE_ACCESS,
    TOKEN_TYPE_REFRESH
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}},
)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: RegisterRequest):
    """Register a new user"""
    # Check if user with email already exists
    existing_email = await User.find_one({"email": user_data.email})
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    existing_username = await User.find_one({"username": user_data.username})
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password
    )
    
    await new_user.insert()
    
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        created_at=new_user.created_at.isoformat()
    )


@router.post("/login", response_model=TokenResponse)
async def login(response: Response, form_data: LoginRequest):
    """Login user and return JWT tokens"""
    # Find user by email
    user = await User.find_one({"email": form_data.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    # Set refresh token in HTTP-only cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 days
    )
    
    return TokenResponse(
        accessToken=access_token,
        refreshToken=refresh_token,
        tokenType="bearer"
    )


@router.post("/logout")
async def logout(
    response: Response, 
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Logout user by blacklisting tokens and clearing cookies"""
    # Get the access token from the Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        access_token = auth_header.replace("Bearer ", "")
        try:
            # Blacklist the access token
            payload, expiration = await decode_token(access_token)
            await blacklist_token(
                token=access_token,
                user_id=current_user.id,
                token_type=TOKEN_TYPE_ACCESS,
                expires_at=expiration
            )
        except Exception:
            # If token is invalid, just continue with logout
            pass
    
    # Get refresh token from cookie and blacklist it
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        try:
            # Blacklist the refresh token
            payload, expiration = await decode_token(refresh_token)
            await blacklist_token(
                token=refresh_token,
                user_id=current_user.id,
                token_type=TOKEN_TYPE_REFRESH,
                expires_at=expiration
            )
        except Exception:
            # If token is invalid, just continue with logout
            pass
    
    # Clear the refresh token cookie
    response.delete_cookie(key="refresh_token")
    
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    response: Response
):
    """Refresh access token using refresh token with token rotation"""
    # Get current user from the refresh token
    try:
        current_user = await get_current_user_from_refresh_token(request)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get the current refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Blacklist the current refresh token (token rotation)
        payload, expiration = await decode_token(refresh_token)
        await blacklist_token(
            token=refresh_token,
            user_id=current_user.id,
            token_type=TOKEN_TYPE_REFRESH,
            expires_at=expiration
        )
        
        # Create new tokens
        new_access_token = create_access_token(data={"sub": current_user.id})
        new_refresh_token = create_refresh_token(data={"sub": current_user.id})
        
        # Set new refresh token in cookie
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=60 * 60 * 24 * 7,  # 7 days
        )
        
        return TokenResponse(
            accessToken=new_access_token,
            refreshToken=new_refresh_token,
            tokenType="bearer"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        created_at=current_user.created_at.isoformat()
    )
