from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt
from langchain.chat_models import init_chat_model
from langchain_core.prompts import PromptTemplate
from typing import TypedDict, List, Dict
from src.utils.state import GeneratorState
from src.utils.constants import MAX_RETRIES
from pydantic import BaseModel, Field, constr
import json
import traceback
from logger import CustomLogger
from dotenv import load_dotenv
load_dotenv()
logger = CustomLogger().get_logger(__name__)
from src.utils.models import model as llm







def human_review(state: GeneratorState):

    # pause execution and return to user
    decision = interrupt(
        {
            "message": "Review generated output",
            "code_or_data": state["llm_output"],
            "errors": state["errors"]
        }
    )

    # decision must be provided when resuming
    state["human_decision"] = decision["action"]
    state["review_notes"] = decision.get("notes", "")

    return state

def after_human(state):

    if state["human_decision"] == "approve":
        return "finish"

    # reject → improve prompt
    state["prompt"] += f"""

    Human feedback:
    {state['review_notes']}

    Regenerate improved version.
    """
    return "retry"

def create_model_from_schema(schema):

    attrs = {}

    for f in schema["fields"]:
        t = f["type"]

        if t == "string":
            attrs[f["name"]] = (str, ...)

        elif t == "int":
            attrs[f["name"]] = (int, ...)

        elif t == "float":
            attrs[f["name"]] = (float, ...)

    return type("DynamicModel", (BaseModel,), attrs)


def retry_or_finish(state):

    if state["validated"]:
        return "finish"

    if state["retries"] >= MAX_RETRIES:
        return "finish"

    state["retries"] += 1

    state["prompt"] += f"""

    Previous output failed:
    {state['errors']}

    Fix and regenerate.
    """
    return "retry"


def validation_router(state):
    if not state["validated"]:
        return "retry"

    # require human review only for code generation
    if state["mode"] in ["M2", "M3"]:
        return "human"

    return "finish"


def validate(state):
    try:
        code_or_data = state["llm_output"]

        # ---------------------------
        # M1 → direct JSON data
        # ---------------------------
        if state["mode"] == "M1":
            records = json.loads(code_or_data)

            if not isinstance(records, list):
                raise ValueError("M1 output must be JSON list")

        # ---------------------------
        # M2 / M3 → executable code
        # ---------------------------
        else:
            namespace = {}

            # safer execution sandbox
            safe_globals = {
                "__builtins__": {
                    "range": range,
                    "len": len,
                    "str": str,
                    "int": int,
                    "float": float,
                    "list": list,
                    "dict": dict,
                    "min": min,
                    "max": max,
                }
            }

            exec(code_or_data, safe_globals, namespace)

            # ---------- M2 ----------
            if state["mode"] == "M2":
                if "generate" not in namespace:
                    raise ValueError("Generated code must define generate(n)")

                records = namespace["generate"](5)

                if not isinstance(records, list):
                    raise ValueError("generate() must return list[dict]")

            # ---------- M3 ----------
            else:
                # Faker provider only needs compilation
                state["validated"] = True
                state["errors"] = None
                return state

        # ---------------------------
        # Schema validation
        # ---------------------------
        Model = create_model_from_schema(state["schema"])

        for r in records:
            if not isinstance(r, dict):
                raise ValueError("Each record must be dict")
            Model(**r)

        state["validated"] = True
        state["errors"] = None

    except Exception:
        state["validated"] = False
        state["errors"] = traceback.format_exc()

    return state

def build_prompt(state: GeneratorState):

    schema_text = "\n".join(
        f"{f['name']} : {f['type']}"
        for f in state["schema"]["fields"]
    )

    constraints_text = "\n".join(state["constraints"])
    rules_text = "\n".join(state["rules"])

    if state["mode"] == "M1":
        prompt = f"""
Generate 20 realistic JSON records.

Schema:
{schema_text}

Constraints:
{constraints_text}

Rules:
{rules_text}

Return JSON array only.
"""

    elif state["mode"] == "M2":
        prompt = f"""
Generate executable Python code.

Write function:
generate(n:int) -> list[dict]

Schema:
{schema_text}

Constraints:
{constraints_text}

Rules:
{rules_text}

No external libraries.
Return code only.
"""

    else:  # M3
        prompt = f"""
Create a Faker provider class for Python Faker.

Schema:
{schema_text}

Constraints:
{constraints_text}

Rules:
{rules_text}

Must follow Faker provider format.
Return code only.
"""

    state["prompt"] = prompt
    return state

def llm_generate(state):
    res = llm.invoke(state["prompt"])
    state["llm_output"] = res.content
    return state