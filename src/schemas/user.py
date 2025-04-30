from pydantic import BaseModel, Field



class UserSchema(BaseModel):
    username: str = Field(..., description="The username of the user")
    email: str = Field(..., description="The email of the user")
    password: str = Field(..., description="The password of the user")