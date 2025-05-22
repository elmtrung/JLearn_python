import pyodbc
import uuid
from app.config import SQL_SERVER_CONNECTION_STRING

def get_db_connection():
    """Establishes a connection to the SQL Server database using the provided connection string."""
    try:
        conn = pyodbc.connect(SQL_SERVER_CONNECTION_STRING)
        return conn
    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        print(f"Database connection error: {sqlstate} - Connection string: {SQL_SERVER_CONNECTION_STRING}")
        return None

def add_transaction_to_db(user_id, collection_id, amount_paid, apptransid):
    """Adds a transaction record to the database."""
    conn = get_db_connection()
    if not conn:
        print(f"Failed to connect to database for apptransid {apptransid}. Transaction not recorded.")
        return False

    cursor = conn.cursor()
    transaction_id = str(uuid.uuid4())
    
    sql = """
    INSERT INTO Transactions (TransactionID, UserID, CollectionID, AmountPaid, TransactionDate)
    VALUES (?, ?, ?, ?, GETDATE())
    """
    try:
        cursor.execute(sql, transaction_id, user_id, collection_id, float(amount_paid))
        conn.commit()
        print(f"Transaction {transaction_id} for apptransid {apptransid} recorded successfully.")
        return True
    except pyodbc.Error as e:
        print(f"Database error while inserting transaction for apptransid {apptransid}: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            cursor.close()
            conn.close()

def get_user_collections(user_id):
    """Gets all collections for a specific user."""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()
        sql = "SELECT CollectionID FROM Transactions WHERE UserID = ?"
        cursor.execute(sql, user_id)
        collections = [row.CollectionID for row in cursor.fetchall()]
        return collections
    except pyodbc.Error as e:
        print(f"Database error while fetching collections for user_id {user_id}: {e}")
        return None
    finally:
        if conn:
            cursor.close()
            conn.close()

def get_admin_metrics():
    """Gets admin metrics including user counts and revenue."""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()
        
        # Get total users and new users in last 30 days
        cursor.execute("""
            SELECT 
                COUNT(*) as total_users,
                SUM(CASE WHEN CreatedAt >= DATEADD(day, -30, GETDATE()) THEN 1 ELSE 0 END) as new_users
            FROM Users
        """)
        user_row = cursor.fetchone()
        total_users = user_row.total_users
        new_users = user_row.new_users

        # Get total revenue
        cursor.execute("SELECT ISNULL(SUM(CAST(AmountPaid as decimal(18,2))), 0) as total_revenue FROM Transactions")
        total_revenue = float(cursor.fetchone().total_revenue)

        # Get user growth for last 6 months
        cursor.execute("""
            SELECT 
                FORMAT(CreatedAt, 'MMM') as month,
                COUNT(*) as count
            FROM Users
            WHERE CreatedAt >= DATEADD(month, -6, GETDATE())
            GROUP BY FORMAT(CreatedAt, 'MMM'), DATEPART(month, CreatedAt)
            ORDER BY DATEPART(month, MIN(CreatedAt))
        """)
        user_growth = [{'month': row.month, 'count': row.count} for row in cursor.fetchall()]

        return {
            'totalUsers': total_users,
            'newUsers': new_users,
            'totalRevenue': total_revenue,
            'userGrowth': user_growth
        }
    except pyodbc.Error as e:
        print(f"Database error while fetching metrics: {e}")
        return None
    finally:
        if conn:
            cursor.close()
            conn.close() 