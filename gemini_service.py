import os
import re
import google.generativeai as genai
from db_manager import get_ddl

def translate_nl_to_sql_with_gemini(api_key: str, user_question: str) -> dict:
    """
    Connects to the Google Gemini API to translate a natural language question
    into a valid SQLite query, leveraging the schema DDL as context.
    """
    if not api_key:
        return {
            "success": False,
            "sql": None,
            "error": "Gemini API Key is missing. Please provide it in the Settings sidebar."
        }
        
    try:
        # Configure Gemini API
        genai.configure(api_key=api_key)
        
        # Get DDL schema
        ddl_schema = get_ddl()
        
        # Construct the system instruction and prompt
        system_instruction = f"""
You are a highly precise Text-to-SQL translator for a financial bot called "CFO-Bot".
Your task is to translate the user's natural language question into a single, valid, highly-optimized SQLite query.

Here is the exact DDL schema of the relational database you have access to:
{ddl_schema}

CRITICAL RULES:
1. ONLY return a SELECT query. You are forbidden from generating INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, or REPLACE queries.
2. Use standard SQLite syntax and functions.
3. Keep column naming clean, and use aliases (AS) to make output tables professional and easy to understand (e.g., SUM(amount) AS total_revenue).
4. If a question is about department spending, you must JOIN the `transactions` and `departments` tables.
5. Return ONLY the raw SQL code. DO NOT wrap the SQL in markdown code blocks like ```sql ... ```. DO NOT include explanations, comments, or extra text. Your entire response must be executable SQL.
"""
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Generate content
        response = model.generate_content(
            contents=[
                {"role": "user", "parts": [
                    f"{system_instruction}\n\nUser Question: {user_question}\nSQL Query:"
                ]}
            ]
        )
        
        sql_output = response.text.strip() if response.text else ""
        
        # Clean up any potential markdown fences that the model might still return
        sql_output = clean_sql_output(sql_output)
        
        if not sql_output:
            return {
                "success": False,
                "sql": None,
                "error": "Gemini returned an empty response. Please try rephrasing your question."
            }
            
        return {
            "success": True,
            "sql": sql_output,
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "sql": None,
            "error": f"Gemini API Error: {str(e)}"
        }

def clean_sql_output(raw_sql: str) -> str:
    """Cleans up markdown code block wrapping, backticks, and comments from LLM output."""
    cleaned = raw_sql.strip()
    
    # Remove markdown code blocks starting with ```sql or ```
    cleaned = re.sub(r"^```sql\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^```\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    
    # Remove leading/trailing quotes/backticks
    cleaned = cleaned.strip("`'\"")
    
    # Ensure there are no leading comments
    cleaned = re.sub(r"^--.*?\n", "", cleaned)
    
    # Clean excessive newlines or semicolons
    cleaned = cleaned.strip()
    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].strip() # We strip trailing semicolon so our safety analyzer controls it
        
    return cleaned
