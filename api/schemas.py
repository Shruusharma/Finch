from pydantic import BaseModel, field_validator

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("message cannot be empty")
        if len(v) > 2000:
            raise ValueError("message too long (max 2000 characters)")
        return v


class ChatResponse(BaseModel):
    response: str
    session_id: str
    agent_used: str