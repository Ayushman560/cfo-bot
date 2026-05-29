import re

# Mock queries library mapping typical natural language questions to safe, highly-optimized SQL
MOCK_QUERIES = [
    {
        "keywords": [r"total.*revenue", r"revenue.*2025", r"how much.*did we earn", r"all.*revenue"],
        "question": "What is our total revenue for 2025?",
        "sql": "SELECT SUM(amount) AS total_revenue FROM transactions WHERE type = 'Revenue' AND date LIKE '2025%';",
        "explanation": "Calculates the sum of all transaction amounts where the transaction type is 'Revenue' and the date starts with '2025'."
    },
    {
        "keywords": [r"top 5.*expense", r"biggest.*expense", r"largest.*expense", r"expensive.*transaction"],
        "question": "Show me our top 5 expenses by amount.",
        "sql": "SELECT date, amount, description, category FROM transactions WHERE type = 'Expense' ORDER BY amount DESC LIMIT 5;",
        "explanation": "Retrieves the date, amount, description, and category from the transactions table, filters for expenses, and orders them in descending order of size, returning the top 5 records."
    },
    {
        "keywords": [r"exceeded.*budget", r"over.*budget", r"budget.*exceed"],
        "question": "Which departments exceeded their budget?",
        "sql": """SELECT d.name AS department, d.budget, ROUND(SUM(t.amount), 2) AS total_spent,
ROUND(SUM(t.amount) - d.budget, 2) AS amount_over
FROM departments d
JOIN transactions t ON d.id = t.department_id
WHERE t.type = 'Expense'
GROUP BY d.id
HAVING total_spent > d.budget;""",
        "explanation": "Joins departments and transactions, groups by department, aggregates all expenses, and filters for departments where total spending exceeds their defined budget limit."
    },
    {
        "keywords": [r"budget.*department", r"show.*budget", r"list.*budget"],
        "question": "Show the budget for each department.",
        "sql": "SELECT name AS department, budget, manager FROM departments ORDER BY budget DESC;",
        "explanation": "Queries the departments table to display department names, allocated budget limits, and their managers, ordered from highest budget to lowest."
    },
    {
        "keywords": [r"cash flow", r"monthly.*balance", r"ledger.*balance", r"treasury"],
        "question": "List our monthly cash flow balances.",
        "sql": "SELECT date, cash_in, cash_out, balance FROM cash_flow_ledger ORDER BY date ASC;",
        "explanation": "Queries the monthly cash flow ledger to trace cash inlets, outlets, and cumulative remaining balance over time, sorted chronologically."
    },
    {
        "keywords": [r"forecast", r"projected.*revenue", r"compare.*forecast"],
        "question": "Compare forecasted revenue vs forecasted expenses.",
        "sql": "SELECT month, projected_revenue, projected_expense, ROUND(projected_revenue - projected_expense, 2) AS projected_net_profit FROM monthly_forecasts ORDER BY month ASC;",
        "explanation": "Examines the monthly_forecasts table to compare future projected revenue against projected expenses, and calculates the projected net margin."
    },
    {
        "keywords": [r"overall.*budget", r"total.*budget.*all", r"sum.*budget"],
        "question": "What is our overall total budget across all departments?",
        "sql": "SELECT SUM(budget) AS total_budget FROM departments;",
        "explanation": "Sums the budget column in the departments table to find the company's total departmental allocations."
    },
    {
        "keywords": [r"category.*spend", r"most.*spent.*category", r"expense.*category", r"where.*spend.*most"],
        "question": "Which category of expenses do we spend the most on?",
        "sql": "SELECT category, ROUND(SUM(amount), 2) AS total_spent FROM transactions WHERE type = 'Expense' GROUP BY category ORDER BY total_spent DESC;",
        "explanation": "Groups transactions of type 'Expense' by category, aggregates the sum of spending in each category, and orders them in descending order to identify the highest spending area."
    },
    {
        "keywords": [r"engineering.*transaction", r"spent.*engineering", r"engineering.*expense"],
        "question": "Show transactions for the Engineering department.",
        "sql": "SELECT t.date, t.amount, t.description, t.category FROM transactions t JOIN departments d ON t.department_id = d.id WHERE d.name = 'Engineering' ORDER BY t.date DESC;",
        "explanation": "Queries transactions linked to the Engineering department, sorted by date in descending order, to show recent expenses."
    },
    {
        "keywords": [r"marketing.*transaction", r"spent.*marketing", r"marketing.*expense"],
        "question": "Show transactions for the Marketing department.",
        "sql": "SELECT t.date, t.amount, t.description, t.category FROM transactions t JOIN departments d ON t.department_id = d.id WHERE d.name = 'Marketing' ORDER BY t.date DESC;",
        "explanation": "Queries transactions linked to the Marketing department, sorted by date in descending order, to show recent expenses."
    }
]

def find_mock_query(nl_query: str) -> dict:
    """
    Fuzzy-matches a natural language query against our deterministic mock query library.
    Returns the query details dict if matched, otherwise None.
    """
    normalized_input = nl_query.lower().strip()
    
    # Try direct keyword search
    for item in MOCK_QUERIES:
        for pattern in item["keywords"]:
            if re.search(pattern, normalized_input):
                return {
                    "matched": True,
                    "question": item["question"],
                    "sql": item["sql"],
                    "explanation": item["explanation"]
                }
                
    return {
        "matched": False,
        "question": nl_query,
        "sql": None,
        "explanation": None
    }

def get_all_suggestions() -> list:
    """Returns the list of beautiful predefined questions for the user to select in UI."""
    return [q["question"] for q in MOCK_QUERIES]
