import streamlit as st
import json
from src.utils.graphs import graph
import pandas as pd

# Set page config

st.set_page_config(page_title="Test Data Agent", layout="wide")

st.title("🤖 AI Test Data Generation Agent")
st.markdown("Select a template to generate synthetic test data using LangGraph.")

# Load templates
with open("src/configs/templates.json", "r") as f:
    templates = json.load(f)

template_names = [t["dataset_config"]["dataset_name"] for t in templates]

col1, col2 = st.columns([2, 2])

with col1:
    st.subheader("Select Template")
    sub_col1, sub_col2 = st.columns([2, 2])
    with sub_col1:
        selected_name = st.selectbox("Select Data Template", template_names)
        selected_template = next(t for t in templates if t["dataset_config"]["dataset_name"] == selected_name)
        
    with sub_col2:

        generate_btn = st.button("Generate Data", type="primary")
    st.subheader("Schema")
    st.json(selected_template)
    
    

if generate_btn:
    # Prepare initial state
    # Merging config and fields for the generator logic
    input_dataset = {**selected_template["dataset_config"], "fields": selected_template.get("fields", [])}
    initial_state = {"dataset": input_dataset, "records": []}
    
    # Run Graph
    with st.spinner("Agent is processing..."):
        final_state = graph.invoke(initial_state)
    
    with col2:
        st.subheader("Generated Data Preview")
        df = pd.DataFrame(final_state["records"])
        st.dataframe(df, use_container_width=True)

        st.success(f"Successfully generated {len(final_state['records'])} records!")