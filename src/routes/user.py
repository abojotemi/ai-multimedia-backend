from fastapi import APIRouter, HTTPException, status, Depends
from src.models.user import User
from src.models.user_settings import UserSettings as UserSettingsModel
from src.schemas.user_settings import (
    UserProfileUpdate,
    UserPasswordUpdate,
    UserSettings,
    UserSettingsResponse
)
from src.utils.auth import get_current_user, verify_password, get_password_hash

router = APIRouter(
    prefix="/user",
    tags=["User"],
    responses={404: {"description": "Not found"}},
)


@router.put("/profile")
async def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update user profile"""
    update_data = profile_data.dict(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    # Check if username is being updated and is unique
    if "username" in update_data and update_data["username"] != current_user.username:
        existing_user = await User.find_one({"username": update_data["username"]})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Check if email is being updated and is unique
    if "email" in update_data and update_data["email"] != current_user.email:
        existing_user = await User.find_one({"email": update_data["email"]})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Update user
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    await current_user.save()
    
    return {
        "message": "Profile updated successfully",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email
        }
    }


@router.put("/password")
async def update_password(
    password_data: UserPasswordUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update user password"""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.password_hash = get_password_hash(password_data.new_password)
    await current_user.save()
    
    return {"message": "Password updated successfully"}


@router.get("/settings", response_model=UserSettingsResponse)
async def get_user_settings(current_user: User = Depends(get_current_user)):
    """Get user settings"""
    # Find user settings or create default
    settings = await UserSettingsModel.find_one({"user_id": current_user.id})
    
    if not settings:
        # Create default settings
        settings = UserSettingsModel(user_id=current_user.id)
        await settings.insert()
    
    return UserSettingsResponse(
        id=current_user.id,
        settings=UserSettings(
            theme=settings.theme,
            notifications_enabled=settings.notifications_enabled,
            default_privacy=settings.default_privacy,
            ai_processing_enabled=settings.ai_processing_enabled,
            display_preferences=settings.display_preferences
        )
    )


@router.put("/settings")
async def update_user_settings(
    settings_data: UserSettings,
    current_user: User = Depends(get_current_user)
):
    """Update user settings"""
    # Find user settings or create default
    settings = await UserSettingsModel.find_one({"user_id": current_user.id})
    
    if not settings:
        # Create settings with provided data
        settings = UserSettingsModel(
            user_id=current_user.id,
            **settings_data.dict()
        )
        await settings.insert()
    else:
        # Update existing settings
        update_data = settings_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(settings, field, value)
        await settings.save()
    
    return {
        "message": "Settings updated successfully",
        "settings": settings_data.dict()
    }