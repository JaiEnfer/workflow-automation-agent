from pydantic import BaseModel, Field
from typing import List

class SummarizeTextArgs(BaseModel):
    text: str = Field(..., min_length=1)

class DraftEmailArgs(BaseModel):
    to: str = Field(..., min_length=3)
    subject: str = Field(..., min_length=1)
    bullet_points: List[str] = Field(default_factory=list)

class CreateTasksArgs(BaseModel):
    tasks: List[str] = Field(default_factory=list)

class ScheduleReminderArgs(BaseModel):
    when: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)
