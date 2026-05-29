import sqlite3
import os
import random
from datetime import datetime, timedelta

DB_FILE = "financials.db"

def get_ddl():
    """Returns the DDL schema for the relational financial database."""
    return """
CREATE TABLE departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    manager TEXT NOT NULL,
    budget REAL NOT NULL
);

CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    amount REAL NOT NULL,
    description TEXT NOT NULL,
    type TEXT CHECK(type IN ('Revenue', 'Expense')) NOT NULL,
    category TEXT NOT NULL,
    department_id INTEGER,
    FOREIGN KEY(department_id) REFERENCES departments(id)
);

CREATE TABLE monthly_forecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT NOT NULL UNIQUE, -- YYYY-MM
    projected_revenue REAL NOT NULL,
    projected_expense REAL NOT NULL
);

CREATE TABLE cash_flow_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    cash_in REAL NOT NULL,
    cash_out REAL NOT NULL,
    balance REAL NOT NULL
);
"""

def initialize_database(force_reseed=False):
    """Initializes the database with schema and high-fidelity financial seed data."""
    db_exists = os.path.exists(DB_FILE)
    
    if force_reseed and db_exists:
        os.remove(DB_FILE)
        db_exists = False
        
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    if not db_exists or force_reseed:
        # Create Tables
        cursor.executescript(get_ddl())
        
                # Seed Departments
        departments = [
            ("Engineering", "Elena Vance", 1200000.00),
            ("Marketing", "Sarah Jenkins", 750000.00),
            ("Sales", "David Miller", 600000.00),
            ("Operations", "Robert Chen", 450000.00),
            ("HR", "Marcus Brody", 200000.00),
            ("Finance & Admin", "Cynthia Ross", 300000.00)
        ]
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.executemany(
            "INSERT INTO departments (name, manager, budget) VALUES (?, ?, ?);",
            departments
        )
        
        # Seed Forecasts (2025-01 through 2025-12)
        months = [f"2025-{m:02d}" for m in range(1, 13)]
        forecasts = []
        base_revenue = 400000.00
        base_expense = 320000.00
        for i, month in enumerate(months):
            # Introduce seasonal growth
            multiplier = 1.0 + (i * 0.03) + random.uniform(-0.02, 0.05)
            forecasts.append((
                month, 
                round(base_revenue * multiplier, 2), 
                round(base_expense * (multiplier * 0.95), 2)
            ))
        cursor.executemany(
            "INSERT INTO monthly_forecasts (month, projected_revenue, projected_expense) VALUES (?, ?, ?);",
            forecasts
        )
        
        # Seed Transactions
        categories = {
            "Expense": ["Infrastructure", "Marketing Campaign", "SaaS Subscriptions", "Hardware & Equipment", "Travel & Events", "Consulting", "Office Operations", "Recruiting"],
            "Revenue": ["Enterprise License", "SaaS Subscription Revenue", "Professional Services", "Partnership Referral"]
        }
        
        descriptions = {
            "Infrastructure": ["AWS Cloud Hosting", "Google Cloud Storage", "Vercel Enterprise Plan", "GitHub Enterprise Seats", "Datadog Observability Stack"],
            "Marketing Campaign": ["Google AdWords Ads", "LinkedIn Paid Lead Generation", "Q1 Brand Video Campaign", "Sponsor Financial Summit 2025", "SEO Consulting Retainer"],
            "SaaS Subscriptions": ["Slack Enterprise Seats", "Salesforce CRM Subscriptions", "Zoom Video Pro", "Figma Design Team License", "Notion Team Plan"],
            "Hardware & Equipment": ["M3 MacBook Pro laptops for Engineering", "Office Standing Desks", "Conference Room AV Suite Upgrade", "Ultra-wide monitors"],
            "Travel & Events": ["Flights to Sales Conference NYC", "Team Building Dinner", "Executive Offsite Lodge", "Hotel stays for onsite workshop"],
            "Consulting": ["External Security Audits", "Tax and Compliance Filing Advisory", "Legal Retainer Fees", "UX Design Consultant Contract"],
            "Office Operations": ["WeWork Rent", "Office Snacks & Catering", "Fiber Internet Line", "Office Cleaning Service", "Ergonomic Chairs"],
            "Recruiting": ["Workday Recruiting Plan", "LinkedIn Recruiter Lite Licenses", "Technical Assessment Tool", "Recruitment Agency Fee"],
            "Enterprise License": ["Enterprise License - Acme Corp", "Global License Agreement - Globex LLC", "Platform License - Umbrella Corp", "Enterprise Core License - Initech"],
            "SaaS Subscription Revenue": ["Monthly SaaS Billing - Tier A Customers", "Monthly SaaS Billing - SMB Tier", "Annual SaaS Plan Renewal - Cyberdyne Systems"],
            "Professional Services": ["Implementation Consultation - Stark Industries", "Migration Support Retainer - Wayne Ent.", "Custom Feature Integration Service"],
            "Partnership Referral": ["Shopify Integration Commission", "Stripe Referral Partnership Reward", "HubSpot Affiliate payout"]
        }
        
        # Start date: 2025-01-01. Generate transaction history.
        start_date = datetime(2025, 1, 1)
        transactions = []
        
        # We want to create 120+ structured transactions
        for i in range(120):
            # Increment days to cover entire year of 2025 and early 2026
            txn_date = (start_date + timedelta(days=i * 3.5 + random.uniform(0, 2))).strftime("%Y-%m-%d")
            
            # Determine Transaction type
            # Standard pattern: Expense is more frequent, but Revenue has higher transaction amounts
            if random.random() < 0.35:
                txn_type = "Revenue"
                dept_id = 3 # Sales department generates revenue
                category = random.choice(categories[txn_type])
                desc = random.choice(descriptions[category])
                amount = round(random.uniform(15000.00, 75000.00), 2)
            else:
                txn_type = "Expense"
                # Expense gets distributed to various departments
                dept_id = random.randint(1, 6) # excluding Sales specifically sometimes or distributing all
                category = random.choice(categories[txn_type])
                desc = random.choice(descriptions[category])
                
                # Align expense amount scale to category
                if category == "Infrastructure":
                    amount = round(random.uniform(5000.00, 28000.00), 2)
                elif category == "Marketing Campaign":
                    amount = round(random.uniform(8000.00, 35000.00), 2)
                elif category == "SaaS Subscriptions":
                    amount = round(random.uniform(1200.00, 9500.00), 2)
                elif category == "Hardware & Equipment":
                    amount = round(random.uniform(2000.00, 15000.00), 2)
                elif category == "Travel & Events":
                    amount = round(random.uniform(800.00, 6500.00), 2)
                else:
                    amount = round(random.uniform(500.00, 5000.00), 2)
            
            transactions.append((txn_date, amount, desc, txn_type, category, dept_id))
            
        cursor.executemany(
            "INSERT INTO transactions (date, amount, description, type, category, department_id) VALUES (?, ?, ?, ?, ?, ?);",
            transactions
        )
        
        # Seed Cash Flow Ledger
        # Compute dynamic values based on our actual generated transactions
        cursor.execute("SELECT date, amount, type FROM transactions ORDER BY date ASC;")
        txns_raw = cursor.fetchall()
        
        ledger_entries = []
        current_balance = 500000.00 # Starting treasury balance
        
        # Group transactions by month
        monthly_groups = {}
        for t_date, t_amt, t_type in txns_raw:
            m_key = t_date[:7] # YYYY-MM
            if m_key not in monthly_groups:
                monthly_groups[m_key] = {"in": 0.0, "out": 0.0}
            if t_type == "Revenue":
                monthly_groups[m_key]["in"] += t_amt
            else:
                monthly_groups[m_key]["out"] += t_amt
                
        # Sort and write ledger
        for m_key in sorted(monthly_groups.keys()):
            cin = round(monthly_groups[m_key]["in"], 2)
            cout = round(monthly_groups[m_key]["out"], 2)
            current_balance = round(current_balance + cin - cout, 2)
            # Record ledger date as end of that month
            l_date = f"{m_key}-28"
            ledger_entries.append((l_date, cin, cout, current_balance))
            
        cursor.executemany(
            "INSERT INTO cash_flow_ledger (date, cash_in, cash_out, balance) VALUES (?, ?, ?, ?);",
            ledger_entries
        )
        
        conn.commit()
    
    conn.close()

if __name__ == "__main__":
    initialize_database(force_reseed=True)
    print("Database financials.db initialized and seeded successfully!")
