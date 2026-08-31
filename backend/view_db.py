import os
from sqlalchemy import create_engine, text

# Get database URL (defaults to local SQLite database if not set)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./threatlens.db")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)

def view_users_table():
    print("\n==========================================================================================================")
    print("                               THREATLENS AI - USER DATABASE TABLE                                        ")
    print("==========================================================================================================")
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT id, full_name, email, role, is_active, created_at FROM users"))
            rows = result.fetchall()
            
            if not rows:
                print("No user records found in database yet. Try registering a user first at http://127.0.0.1:8000/docs !")
                print("==========================================================================================================\n")
                return

            # Print Table Header
            header = f"| {'ID':<4} | {'FULL NAME':<25} | {'EMAIL':<30} | {'ROLE':<18} | {'ACTIVE':<6} |"
            divider = "-" * len(header)
            
            print(divider)
            print(header)
            print(divider)
            
            # Print Rows
            for row in rows:
                user_id, full_name, email, role, is_active, created_at = row
                print(f"| {user_id:<4} | {full_name:<25} | {email:<30} | {role:<18} | {str(is_active):<6} |")
            
            print(divider)
            print(f"Total Users Found: {len(rows)}\n")

    except Exception as e:
        print(f"Error querying database table: {e}")

if __name__ == "__main__":
    view_users_table()
