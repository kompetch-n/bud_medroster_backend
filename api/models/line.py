from pydantic import BaseModel

class SendLineRequest(BaseModel):
    to: str
    message: str
