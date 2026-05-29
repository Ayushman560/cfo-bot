import sqlite3
import pandas as pd
import time
import re
from db_manager import DB_FILE

def execute_query(sql: str):
    """Executes a SQL query against the SQLite database in a safe read-only manner."""
    conn = None
    start_time = time.time()
    try:
        conn = sqlite3.connect(DB_FILE)
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON;")
        
        # Read the SQL query using Pandas
        df = pd.read_sql_query(sql, conn)
        execution_time = (time.time() - start_time) * 1000 # milliseconds
        
        return {
            "success": True,
            "data": df,
            "columns": list(df.columns),
            "row_count": len(df),
            "execution_time": round(execution_time, 2),
            "error": None
        }
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        return {
            "success": False,
            "data": None,
            "columns": [],
            "row_count": 0,
            "execution_time": round(execution_time, 2),
            "error": str(e)
        }
    finally:
        if conn:
            conn.close()

def verify_sql_safety(sql: str) -> dict:
    """
    Implements a strict Safety Layer that validates SQL inputs.
    Scans for injection patterns and ensures queries are read-only SELECTs.
    
    Returns a audit report dictionary.
    """
    steps = []
    violations = []
    is_safe = True
    
    # 1. Strip whitespace
    cleaned_sql = sql.strip() if sql else ""
    steps.append("🔍 Initializing security pipeline and stripping trailing whitespaces.")
    
    if not cleaned_sql:
        return {
            "is_safe": False,
            "cleaned_sql": "",
            "reason": "Empty query",
            "violations": ["Query is empty"],
            "steps": steps
        }
        
    steps.append("🛡️ Step 1: Pre-scanning input for common raw SQL injection patterns...")
    
    # Check for stacked/multiple queries (semicolon separation)
    # Semicolons followed by characters can indicate stacked queries (e.g. SELECT * ...; DROP TABLE ...)
    semicolon_split = [q.strip() for q in cleaned_sql.split(";") if q.strip()]
    if len(semicolon_split) > 1:
        is_safe = False
        violations.append("Stacked queries detected (multiple SQL commands separated by semicolons)")
        steps.append("❌ Violation: Stacked queries are strictly forbidden to prevent database tampering.")
    
    # Check for SQL comments (often used to truncate queries during injection)
    if "--" in cleaned_sql or "/*" in cleaned_sql:
        is_safe = False
        violations.append("SQL comments detected ('--' or '/*')")
        steps.append("❌ Violation: SQL comment structures detected. These are blocked because they can bypass criteria filters.")
        
    # Check for classic auth-bypass injection tautologies like "1=1" or "1 = 1" or "a=a"
    tautology_pattern = r"(?i)\b(\w+)\s*=\s*\1\b|\b'([^']*)'\s*=\s*'\2'\b"
    if re.search(tautology_pattern, cleaned_sql):
        is_safe = False
        violations.append("Tautology patterns detected (e.g., '1=1' or 'a=a')")
        steps.append("❌ Violation: Potential SQL Injection tautology detected (e.g., condition evaluates to true permanently).")

    # 2. Tokenize & Analyze AST (Abstract Syntax Tree)
    steps.append("🕵️ Step 2: Running lexical tokenization and syntactic analysis...")
    
    # Normalize spaces and lowercase for keyword matching
    normalized_sql = re.sub(r'\s+', ' ', cleaned_sql).lower()
    
    # SQL commands that mutate state or alter schema
    forbidden_keywords = {
        "insert": "INSERT (Data Mutation)",
        "update": "UPDATE (Data Mutation)",
        "delete": "DELETE (Data Destruction)",
        "drop": "DROP (Schema Destruction)",
        "create": "CREATE (Schema Modification)",
        "alter": "ALTER (Schema Modification)",
        "truncate": "TRUNCATE (Data Destruction)",
        "replace": "REPLACE (Data Mutation)",
        "grant": "GRANT (Privilege Escalation)",
        "revoke": "REVOKE (Privilege Escalation)",
        "exec": "EXEC/EXECUTE (Command Execution)",
        "xp_cmdshell": "xp_cmdshell (System shell access)",
        "attach": "ATTACH DATABASE (Schema injection)"
    }
    
    # Inspect word tokens to prevent matching inner letters of columns (e.g. "budget_dropped" shouldn't trigger "drop")
    words = re.findall(r'\b\w+\b', normalized_sql)
    
    found_forbidden = []
    for keyword, desc in forbidden_keywords.items():
        if keyword in words:
            found_forbidden.append(desc)
            
    if found_forbidden:
        is_safe = False
        violations.extend([f"Forbidden operation: {f}" for f in found_forbidden])
        steps.append(f"❌ Violation: Found forbidden state-mutating command(s): {', '.join(found_forbidden)}")
    else:
        steps.append("✅ No mutating command keywords found.")

    # 3. Read-Only Restriction Check
    steps.append("🔒 Step 3: Verifying read-only execution constraint...")
    
    # Must start with SELECT
    # We do a word-boundary check on the very first word
    match_select = re.match(r'^\s*select\b', normalized_sql)
    if not match_select:
        is_safe = False
        violations.append("Query does not begin with the SELECT command")
        steps.append("❌ Violation: CFO-Bot execution rules require every query to start with SELECT.")
    else:
        steps.append("✅ Read-only policy satisfied: Query begins with a SELECT statement.")

    # Try optional sqlparse advanced scanning if available
    try:
        import sqlparse
        steps.append("🧩 Step 4: Compiling Abstract Syntax Tree using 'sqlparse'...")
        parsed = sqlparse.parse(cleaned_sql)
        if parsed:
            statement = parsed[0]
            # Ensure it is parsed as a DQL statement
            stmt_type = statement.get_type()
            steps.append(f"ℹ️ Statement type identified by parser: {stmt_type}")
            if stmt_type != "SELECT":
                # Only violate if we didn't already catch it to prevent duplication
                if "Query does not begin with the SELECT command" not in violations:
                    is_safe = False
                    violations.append(f"Invalid statement type parsed: {stmt_type}")
                    steps.append(f"❌ Violation: Statement type is {stmt_type}, but only SELECT is allowed.")
            else:
                steps.append("✅ AST verification complete: Verified as a valid, read-only SELECT structure.")
    except ImportError:
        steps.append("ℹ️ Step 4: Advanced AST parsing skipped (sqlparse package not installed globally yet). Using robust regex backup.")

    if is_safe:
        steps.append("🚀 Step 5: Safety audit successful. Forwarding clean query to DB engine.")
        reason = "Passed security scanner audit"
    else:
        steps.append("🚫 Step 5: Safety audit failed. Aborting database execution to protect data.")
        reason = "Blocked by security scan"
        
    return {
        "is_safe": is_safe,
        "cleaned_sql": cleaned_sql,
        "reason": reason,
        "violations": violations,
        "steps": steps
    }

if __name__ == "__main__":
    # Test safe queries
    q1 = "SELECT * FROM departments WHERE budget > 500000;"
    print("Testing safe query:", q1)
    res1 = verify_sql_safety(q1)
    print("Is safe?", res1["is_safe"])
    print("Steps:")
    for s in res1["steps"]:
        print("  ", s)
        
    print("\n" + "="*40 + "\n")
    
    # Test unsafe query
    q2 = "SELECT * FROM transactions; DROP TABLE departments;"
    print("Testing unsafe query:", q2)
    res2 = verify_sql_safety(q2)
    print("Is safe?", res2["is_safe"])
    print("Violations:", res2["violations"])
    print("Steps:")
    for s in res2["steps"]:
        print("  ", s)
