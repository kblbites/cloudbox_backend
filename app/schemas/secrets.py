from typing import Literal

from pydantic import BaseModel, Field


class SecretOut(BaseModel):
    id: int
    name: str
    type: str


class SecretCreatePassword(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)


class SecretCreateSsh(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    public_key: str = Field(..., min_length=32)


class PlanOptionsOut(BaseModel):
    vcpu_options: list[int]
    ram_options: list[int]
    storage_options: list[int]
