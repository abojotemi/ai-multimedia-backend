from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime

from src.models.user import User
from src.schemas.user import UserSchema
from src.schemas.user_settings import UserProfileUpdate, UserPasswordUpdate
from src.service.auth import auth_service
from src.utils.auth import get_current_user, verify_password, get_password_hash

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("/")
def settings_home():
    return {"message": "Welcome to settings"}

@router.post("/create_user", response_model=User)
async def create_user(user: UserSchema):
    user = await auth_service.create_user(user)  
    return user

@router.put("/update_profile")
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update user profile from settings page"""
    update_data = profile_data.model_dump(exclude_unset=True)
    
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
    
    # Update the updated_at timestamp
    current_user.updated_at = datetime.now()
    await current_user.save()
    
    return {
        "message": "Profile updated successfully",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email
        }
    }

@router.put("/update_password")
async def update_user_password(
    password_data: UserPasswordUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update user password from settings page"""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.password_hash = get_password_hash(password_data.new_password)
    
    # Update the updated_at timestamp
    current_user.updated_at = datetime.now()
    await current_user.save()
    
    return {"message": "Password updated successfully"}