import sys
import traceback
import os
import json
import re
from io import StringIO
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

# Initialize FastAPI App
app = FastAPI()

# Enable CORS (Required for the grader to test your endpoint)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models for API Requests & Responses ---
class CodeRequest(BaseModel):
    code: str

class CodeResponse(BaseModel):
    error: List[int]
    result: str

class ErrorAnalysis(BaseModel):
    error_lines: List[int]

# --- Configure AI Pipe Client ---
# We use the standard OpenAI client but override the base_url and api_key
client = OpenAI(
    base_url="https://aipipe.org/openrouter/v1",
    api_key=os.environ.get("AIPIPE_TOKEN", "fallback_if_not_set")
)

# --- Part 1: Tool Function ---
def execute_python_code(code: str) -> dict:
    """
    Execute Python code and return exact output.
    Returns: {"success": bool, "output": str}
    """
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    try:
        # Execute code in an empty dictionary to isolate scope
        exec(code, {})
        output = sys.stdout.getvalue()
        return {"success": True, "output": output}

    except Exception as e:
        # Get full traceback
        output = traceback.format_exc()
        
        # CLEANUP: Remove internal main.py frames from the traceback
        # so the LLM and the regex only see the executed <string> error
        string_file_index = output.find('File "<string>"')
        if string_file_index != -1:
            header = "Traceback (most recent call last):\n  "
            output = header + output[string_file_index:]
            
        return {"success": False, "output": output}

    finally:
        sys.stdout = old_stdout

# --- Part 2: AI Error Analysis ---
def analyze_error_with_ai(code: str, traceback_str: str) -> List[int]:
    """
    Use LLM with AI Pipe to identify error line numbers, with fallback.
    """
    prompt = f"""
    Analyze this Python code and its error traceback.
    Identify the line number(s) where the error occurred.

    CODE:
    {code}

    TRACEBACK:
    {traceback_str}

    Return ONLY a JSON object with a single key "error_lines" containing a list of integers. Example: {{"error_lines": [1]}}
    Do NOT wrap the JSON in markdown blocks. If it says 'line X', the error is X.
    """

    try:
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-lite-001",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        # Get response and strip any hallucinated markdown wrappers
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        result = ErrorAnalysis.model_validate_json(content)
        return result.error_lines
        
    except Exception as e:
        print(f"LLM API Error/Parse Error: {e}")
        
        # Bulletproof fallback: Find the first instance of 'line X' in the cleaned traceback
        match = re.search(r'line (\d+)', traceback_str)
        if match:
            return [int(match.group(1))]
        return []

# --- Part 3: The API Endpoint ---
@app.post("/code-interpreter", response_model=CodeResponse)
def code_interpreter(request: CodeRequest):
    """
    Accepts Python code, runs it, and automatically analyzes 
    line numbers using an LLM if an error occurs.
    """
    # 1. Execute the code
    exec_status = execute_python_code(request.code)
    
    # 2. Check Success
    if exec_status["success"]:
        return CodeResponse(error=[], result=exec_status["output"])
    
    # 3. If there is an error, invoke the AI Agent via AI Pipe
    error_lines = analyze_error_with_ai(request.code, exec_status["output"])

    # 4. Return formatted response
    return CodeResponse(error=error_lines, result=exec_status["output"])
