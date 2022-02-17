from pydantic import BaseModel

class Nmap_input(BaseModel):
    url: str
    class Config:
        orm_mode = True