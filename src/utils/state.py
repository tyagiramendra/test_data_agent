from typing import TypedDict, List, Dict

from typing import TypedDict, Optional, Dict, List
from pydantic import BaseModel, Field, constr
import json, traceback

class DataState(TypedDict):
    dataset: Dict
    records: List


class GeneratorState(TypedDict):
    schema: Dict
    constraints: List[str]
    rules: List[str]
    locale: str
    framework: str
    mode: str

    prompt: Optional[str]
    llm_output: Optional[str]

    validated: bool
    errors: Optional[str]
    retries: int

    # NEW
    human_decision: Optional[str]   # approve/reject
    review_notes: Optional[str]