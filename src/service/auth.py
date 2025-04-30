# from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from src.models.user import User
from src.schemas.user import UserSchema
from src.utils import auth

class AuthService:
    async def get_user(self, email: str) -> User | None:
        user = await User.find_one(User.email == email)
        return user

    async def _user_exists(self, email: str) -> bool:
        user = await self.get_user(email)
        return user is not None
    
    async def create_user(self, user_data: UserSchema) -> User:
        data = user_data.model_dump()
        data['password_hash'] = auth.hash_password(data['password'])
        user = User(**data)
        await user.create()
        return user
    
    async def get_current_user(
        self,
    ) -> User:
        ...
    async def authenticate_user(
        self, user_data: OAuth2PasswordRequestForm
    ):
        ...

auth_service = AuthService()
