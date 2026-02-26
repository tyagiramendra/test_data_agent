from langgraph.graph import StateGraph, START, END
from src.utils.generators import *
from src.utils.state import DataState
from src.utils.state import GeneratorState
from src.utils.models import model as llm
from src.utils.prompts import *
from src.utils.nodes import *


# ---------- Nodes ----------

def router(state: DataState):
    return state["dataset"]["type"]


def static_node(state):
    return {"records": generate_static(state["dataset"])}


def dynamic_node(state):
    return {"records": generate_dynamic(state["dataset"])}


def boundary_node(state):
    return {"records": generate_boundary(state["dataset"])}


def combinational_node(state):
    return {"records": generate_combinational(state["dataset"])}


def exporter(state):
    import json
    name = state["dataset"]["dataset_name"]
    # with open(f"{name}.json", "w") as f:
    #     json.dump(state["records"], f, indent=2)
    return state


# ---------- Graph ----------

builder = StateGraph(DataState)

builder.add_node("static", static_node)
builder.add_node("dynamic", dynamic_node)
builder.add_node("boundary", boundary_node)
builder.add_node("combinational", combinational_node)
builder.add_node("export", exporter)

builder.set_conditional_entry_point(
    router,
    {
        "static": "static",
        "dynamic": "dynamic",
        "boundary": "boundary",
        "combinational": "combinational"
    }
)

builder.add_edge("static", "export")
builder.add_edge("dynamic", "export")
builder.add_edge("boundary", "export")
builder.add_edge("combinational", "export")
builder.add_edge("export", END)

graph = builder.compile()


# Data Generator

genrator_builder = StateGraph(GeneratorState)

genrator_builder.add_node("build_prompt", build_prompt)
genrator_builder.add_node("llm_generate", llm_generate)
genrator_builder.add_node("validate", validate)
genrator_builder.add_node("human_review", human_review)

genrator_builder.set_entry_point("build_prompt")

genrator_builder.add_edge("build_prompt", "llm_generate")
genrator_builder.add_edge("llm_generate", "validate")

genrator_builder.add_conditional_edges(
    "validate",
    validation_router,
    {
        "retry": "llm_generate",
        "human": "human_review",
        "finish": END
    }
)

genrator_builder.add_conditional_edges(
    "human_review",
    after_human,
    {
        "retry": "llm_generate",
        "finish": END
    }
)

gen_agent = builder.compile()

if __name__ == "__main__":
    pass