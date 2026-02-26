# Step 1: Define tools 
import json
import os

from langchain_community.tools.python.tool import PythonREPLTool


repl_tool = PythonREPLTool()
tools = [repl_tool]


if __name__ == "__main__":
    code=print("Hello World")
    repl_tool.invoke(json.loads(code))
