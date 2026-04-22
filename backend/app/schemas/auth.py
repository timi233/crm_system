from pydantic import BaseModel


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class FeishuLoginRequest(BaseModel):
    code: str
    state: str


class FeishuLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class AuthCapabilitiesResponse(BaseModel):
    role: str
    capabilities: dict[str, bool]
