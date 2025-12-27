from pydantic import BaseModel
from typing import List, Optional

class JobDetails(BaseModel):
    url: str
    title: str
    company: str
    country: str
    seniority: str
    category: str
    responsibilities: Optional[List[str]]
    requirements: Optional[List[str]]
    skills: Optional[List[str]]
    employment_term: str
    employment_type: str
    embedding: List[float]