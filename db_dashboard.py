import streamlit as st
import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv
import plotly.express as px
from datetime import datetime
import re
import streamlit.components.v1 as components
import base64
from io import BytesIO

# Load environment variables from .env file
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="CVFlow DB Dashboard",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for improved appearance
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 700;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #0D47A1;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .metric-container {
        background-color: #f0f7ff;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        text-align: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .highlight {
        color: #1E88E5;
        font-weight: 600;
    }
    .table-container {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .stButton button {
        background-color: #1E88E5;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stButton button:hover {
        background-color: #0D47A1;
    }
    .delete-button button {
        background-color: #F44336;
    }
    .delete-button button:hover {
        background-color: #D32F2F;
    }
    .success-message {
        background-color: #C8E6C9;
        color: #2E7D32;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .error-message {
        background-color: #FFCDD2;
        color: #C62828;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    div[data-testid="stSidebar"] {
        background-color: #f0f7ff;
    }
    div.stSelectbox > div > div {
        background-color: #ffffff;
        border-radius: 5px;
    }
    .footer {
        text-align: center;
        color: #757575;
        margin-top: 20px;
        padding: 10px;
        font-size: 0.8rem;
    }
    /* Progress bar styling */
    div.stProgress > div > div {
        background-color: #1E88E5;
    }
</style>
""", unsafe_allow_html=True)

# Create database connection
def create_connection():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME', 'postgres'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )
        return conn
    except Exception as e:
        st.error(f"Error connecting to PostgreSQL: {e}")
        return None

# Get table schema
def get_table_schema(conn, table_name):
    try:
        cursor = conn.cursor()
        query = f"""
        SELECT column_name, data_type, 
               is_nullable, column_default,
               character_maximum_length
        FROM information_schema.columns
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position;
        """
        cursor.execute(query)
        columns = cursor.fetchall()
        cursor.close()
        return columns
    except Exception as e:
        st.error(f"Error getting schema for {table_name}: {e}")
        return []

# Get foreign key constraints
def get_foreign_keys(conn, table_name):
    try:
        cursor = conn.cursor()
        query = f"""
        SELECT
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM
            information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE
            tc.constraint_type = 'FOREIGN KEY' AND
            tc.table_name = '{table_name}';
        """
        cursor.execute(query)
        foreign_keys = cursor.fetchall()
        cursor.close()
        
        fk_dict = {}
        for fk in foreign_keys:
            column_name, foreign_table, foreign_column = fk
            fk_dict[column_name] = (foreign_table, foreign_column)
        
        return fk_dict
    except Exception as e:
        st.error(f"Error getting foreign keys for {table_name}: {e}")
        return {}

# Get all tables in the database
def get_tables(conn):
    try:
        cursor = conn.cursor()
        query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
        """
        cursor.execute(query)
        tables = cursor.fetchall()
        cursor.close()
        return [table[0] for table in tables]
    except Exception as e:
        st.error(f"Error getting tables: {e}")
        return []

# Get all records from a table
def get_table_data(conn, table_name, limit=None, where_clause=None):
    try:
        cursor = conn.cursor()
        limit_clause = f"LIMIT {limit}" if limit else ""
        where_str = f"WHERE {where_clause}" if where_clause else ""
        
        query = f"""
        SELECT * FROM {table_name}
        {where_str}
        ORDER BY (SELECT MIN(column_name) FROM information_schema.columns 
                  WHERE table_name='{table_name}' AND column_name LIKE '%id')
        {limit_clause};
        """
        cursor.execute(query)
        records = cursor.fetchall()
        
        # Get column names
        column_names = [desc[0] for desc in cursor.description]
        
        cursor.close()
        
        # Convert to DataFrame
        df = pd.DataFrame(records, columns=column_names)
        return df
    except Exception as e:
        st.error(f"Error retrieving data from {table_name}: {e}")
        return pd.DataFrame()

# Get foreign key reference values
def get_foreign_key_options(conn, foreign_table, foreign_column):
    try:
        cursor = conn.cursor()
        
        # Try to find a descriptive column like name, description, title, etc.
        cursor.execute(f"""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = '{foreign_table}' 
            AND (column_name LIKE '%name%' OR column_name LIKE '%title%' OR column_name LIKE '%description%')
            LIMIT 1;
        """)
        
        descriptive_column = cursor.fetchone()
        
        if descriptive_column:
            query = f"""
            SELECT {foreign_column}, {descriptive_column[0]} 
            FROM {foreign_table} 
            ORDER BY {descriptive_column[0]};
            """
            cursor.execute(query)
            options = cursor.fetchall()
            cursor.close()
            # Return as dict with ID as key and descriptive column as value
            return {str(option[0]): f"{option[0]} - {option[1]}" for option in options}
        else:
            # If no descriptive column found, just get the IDs
            query = f"""
            SELECT {foreign_column} FROM {foreign_table} ORDER BY {foreign_column};
            """
            cursor.execute(query)
            options = cursor.fetchall()
            cursor.close()
            return {str(option[0]): str(option[0]) for option in options}
    except Exception as e:
        st.error(f"Error getting foreign key options for {foreign_table}.{foreign_column}: {e}")
        return {}

# Insert record into table
def insert_record(conn, table_name, values):
    try:
        cursor = conn.cursor()
        columns = ', '.join(values.keys())
        placeholders = ', '.join(['%s'] * len(values))
        
        query = f"""
        INSERT INTO {table_name} ({columns})
        VALUES ({placeholders})
        RETURNING *;
        """
        
        cursor.execute(query, list(values.values()))
        inserted_id = cursor.fetchone()[0]  # Get the first column (usually the ID)
        conn.commit()
        cursor.close()
        return True, inserted_id
    except Exception as e:
        conn.rollback()
        return False, str(e)

# Update record in table
def update_record(conn, table_name, record_id, id_column, values):
    try:
        cursor = conn.cursor()
        set_clause = ', '.join([f"{col} = %s" for col in values.keys()])
        
        query = f"""
        UPDATE {table_name}
        SET {set_clause}
        WHERE {id_column} = %s
        RETURNING *;
        """
        
        params = list(values.values()) + [record_id]
        cursor.execute(query, params)
        conn.commit()
        cursor.close()
        return True, "Record updated successfully"
    except Exception as e:
        conn.rollback()
        return False, str(e)

# Delete record from table
def delete_record(conn, table_name, record_id, id_column):
    try:
        cursor = conn.cursor()
        query = f"""
        DELETE FROM {table_name}
        WHERE {id_column} = %s
        RETURNING *;
        """
        
        cursor.execute(query, [record_id])
        deleted = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        return True, "Record deleted successfully" if deleted else "No record found to delete"
    except Exception as e:
        conn.rollback()
        return False, str(e)

# Get table row count
def get_table_count(conn, table_name):
    try:
        cursor = conn.cursor()
        query = f"SELECT COUNT(*) FROM {table_name};"
        cursor.execute(query)
        count = cursor.fetchone()[0]
        cursor.close()
        return count
    except Exception as e:
        st.error(f"Error getting count for {table_name}: {e}")
        return 0

# Get primary key column
def get_primary_key(conn, table_name):
    try:
        cursor = conn.cursor()
        query = f"""
        SELECT kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        WHERE tc.table_name = '{table_name}'
        AND tc.constraint_type = 'PRIMARY KEY';
        """
        cursor.execute(query)
        pk = cursor.fetchone()
        cursor.close()
        return pk[0] if pk else None
    except Exception as e:
        st.error(f"Error getting primary key for {table_name}: {e}")
        return None

# Generate a form input based on column type
def generate_form_input(col_name, data_type, is_nullable, col_default, char_max_length, foreign_keys, conn, existing_value=None):
    if col_name in foreign_keys:
        foreign_table, foreign_column = foreign_keys[col_name]
        options = get_foreign_key_options(conn, foreign_table, foreign_column)
        
        # Add empty option if nullable
        if is_nullable == 'YES':
            options[""] = "--- Select ---"
        
        # Convert existing value to string for selectbox
        if existing_value is not None:
            existing_value = str(existing_value) if existing_value != "" else ""
        
        selected = st.selectbox(
            f"{col_name} ({foreign_table} reference)", 
            options=list(options.keys()),
            format_func=lambda x: options.get(x, x),
            index=list(options.keys()).index(existing_value) if existing_value in options.keys() else 0
        )
        
        # Convert empty string back to None for nullable columns
        if selected == "" and is_nullable == 'YES':
            return None
        
        # Try to convert to int/float if appropriate
        try:
            if data_type in ['integer', 'smallint', 'bigint']:
                return int(selected) if selected else None
            return selected
        except:
            return selected
    
    # Handle different data types
    if data_type in ['integer', 'smallint', 'bigint']:
        if existing_value is None and col_default and col_default.startswith('nextval'):
            # This is likely an auto-incrementing ID column
            st.text_input(col_name, value="Auto-generated", disabled=True)
            return None
        else:
            return st.number_input(col_name, value=int(existing_value) if existing_value is not None else 0, step=1)
    
    elif data_type in ['numeric', 'decimal', 'real', 'double precision']:
        if existing_value is None:
            existing_value = 0.0
        return st.number_input(col_name, value=float(existing_value), step=0.01, format="%.2f")
    
    elif data_type == 'boolean':
        default_value = False
        if existing_value is not None:
            if isinstance(existing_value, bool):
                default_value = existing_value
            else:
                default_value = str(existing_value).lower() in ['true', 't', 'yes', 'y', '1']
        return st.checkbox(col_name, value=default_value)
    
    elif data_type == 'date':
        if existing_value is not None:
            if isinstance(existing_value, str):
                try:
                    existing_value = datetime.strptime(existing_value, '%Y-%m-%d').date()
                except:
                    existing_value = datetime.now().date()
            elif not hasattr(existing_value, 'date'):
                existing_value = datetime.now().date()
        else:
            existing_value = datetime.now().date()
        return st.date_input(col_name, value=existing_value)
    
    elif data_type in ['timestamp', 'timestamptz', 'timestamp with time zone', 'timestamp without time zone']:
        if existing_value is not None:
            if isinstance(existing_value, str):
                try:
                    existing_value = datetime.strptime(existing_value, '%Y-%m-%d %H:%M:%S')
                except:
                    try:
                        existing_value = datetime.strptime(existing_value, '%Y-%m-%d %H:%M:%S.%f')
                    except:
                        existing_value = datetime.now()
            elif not isinstance(existing_value, datetime):
                existing_value = datetime.now()
        else:
            existing_value = datetime.now()
        
        date_val = st.date_input(f"{col_name} (date)", value=existing_value.date())
        time_val = st.time_input(f"{col_name} (time)", value=existing_value.time())
        
        # Combine date and time
        combined = datetime.combine(date_val, time_val)
        return combined
    
    elif data_type == 'time':
        if existing_value is not None:
            if isinstance(existing_value, str):
                try:
                    # Parse the time string
                    hr, min, sec = map(int, existing_value.split(':'))
                    existing_value = datetime.now().replace(hour=hr, minute=min, second=sec).time()
                except:
                    existing_value = datetime.now().time()
            elif not hasattr(existing_value, 'hour'):
                existing_value = datetime.now().time()
        else:
            existing_value = datetime.now().time()
        
        return st.time_input(col_name, value=existing_value)
    
    elif data_type == 'text':
        return st.text_area(col_name, value=existing_value if existing_value is not None else "")
    
    elif col_name.endswith('_url') or col_name.endswith('_image_url'):
        return st.text_input(col_name, value=existing_value if existing_value is not None else "")
    
    else:  # Default to text input for other types (varchar, char, etc.)
        max_chars = int(char_max_length) if char_max_length else None
        return st.text_input(
            col_name, 
            value=existing_value if existing_value is not None else "",
            max_chars=max_chars
        )

# Validate data against schema
def validate_data(values, schema, foreign_keys):
    errors = []
    
    for col in schema:
        col_name, data_type, is_nullable, col_default, char_max_length = col
        
        # Skip auto-generated columns
        if col_default and 'nextval' in str(col_default):
            continue
            
        # Check required fields
        if is_nullable == 'NO' and (col_name not in values or values[col_name] is None or values[col_name] == ''):
            errors.append(f"{col_name} is required")
            continue
            
        # If field is not in values or is None/empty and nullable, continue
        if col_name not in values or values[col_name] is None or values[col_name] == '':
            if is_nullable == 'YES':
                continue
                
        # Type validation
        if col_name in values and values[col_name] is not None:
            try:
                # Integer validation
                if data_type in ['integer', 'smallint', 'bigint']:
                    if not isinstance(values[col_name], int) and not str(values[col_name]).isdigit():
                        errors.append(f"{col_name} must be an integer")
                
                # Float validation
                elif data_type in ['numeric', 'decimal', 'real', 'double precision']:
                    try:
                        float(values[col_name])
                    except:
                        errors.append(f"{col_name} must be a number")
                
                # Email validation
                elif col_name == 'email' or col_name.endswith('_email'):
                    if not re.match(r"[^@]+@[^@]+\.[^@]+", str(values[col_name])):
                        errors.append(f"{col_name} must be a valid email address")
                
                # Phone validation
                elif col_name == 'phone' or col_name.endswith('_phone'):
                    if not re.match(r"^\+?[0-9]{8,15}$", str(values[col_name])):
                        errors.append(f"{col_name} must be a valid phone number (8-15 digits, may start with +)")
                
                # Length validation for varchar/char
                elif data_type.startswith('character varying') and char_max_length:
                    if len(str(values[col_name])) > int(char_max_length):
                        errors.append(f"{col_name} must be at most {char_max_length} characters")
            
            except Exception as e:
                errors.append(f"Error validating {col_name}: {str(e)}")
    
    return errors

# Generate dashboard metrics
def generate_metrics(conn, tables):
    total_tables = len(tables)
    total_records = sum([get_table_count(conn, table) for table in tables])
    
    # Find latest record
    latest_record = None
    latest_table = None
    latest_date = None
    
    for table in tables:
        try:
            cursor = conn.cursor()
            # Check if the table has a timestamp column (created_at or similar)
            cursor.execute(f"""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = '{table}' 
                AND (column_name LIKE '%created_at%' OR column_name LIKE '%date%' OR column_name LIKE '%timestamp%')
                AND data_type LIKE '%timestamp%'
                LIMIT 1;
            """)
            
            date_col = cursor.fetchone()
            
            if date_col:
                query = f"""
                SELECT *, {date_col[0]} FROM {table}
                ORDER BY {date_col[0]} DESC
                LIMIT 1;
                """
                cursor.execute(query)
                record = cursor.fetchone()
                
                if record and record[-1]:  # The date should be the last element
                    if latest_date is None or record[-1] > latest_date:
                        latest_date = record[-1]
                        latest_record = record
                        latest_table = table
            
            cursor.close()
        except:
            continue
    
    # Get records by date info for one of the main tables (users if it exists)
    time_series_data = None
    if 'users' in tables:
        try:
            cursor = conn.cursor()
            query = """
            SELECT DATE_TRUNC('month', created_at) AS month, COUNT(*) as count
            FROM users
            GROUP BY month
            ORDER BY month;
            """
            cursor.execute(query)
            time_series_records = cursor.fetchall()
            cursor.close()
            
            if time_series_records:
                time_series_data = pd.DataFrame(time_series_records, columns=['month', 'count'])
                time_series_data['month'] = time_series_data['month'].dt.strftime('%Y-%m')
        except:
            pass
    
    return {
        'total_tables': total_tables,
        'total_records': total_records,
        'latest_record': latest_record,
        'latest_table': latest_table,
        'latest_date': latest_date,
        'time_series_data': time_series_data
    }

# Export table to CSV
def export_table_to_csv(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="table_export.csv" class="download-link">Download CSV</a>'
    return href

# Export table to Excel
def export_table_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    
    excel_data = output.getvalue()
    b64 = base64.b64encode(excel_data).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="table_export.xlsx" class="download-link">Download Excel</a>'
    return href

# Main application
def main():
    st.sidebar.image("https://raw.githubusercontent.com/streamlit/streamlit/master/examples/data/logo.png", width=200)
    st.sidebar.markdown("## Database Explorer")
    
    # Database connection
    conn = create_connection()
    if not conn:
        st.error("Failed to connect to the database. Please check your environment variables.")
        return
    
    # Get all tables
    tables = get_tables(conn)
    
    if not tables:
        st.warning("No tables found in the database.")
        return
    
    # App modes
    app_mode = st.sidebar.selectbox(
        "Choose Mode",
        ["Dashboard", "Table Explorer", "Data Management"]
    )
    
    if app_mode == "Dashboard":
        display_dashboard(conn, tables)
    
    elif app_mode == "Table Explorer":
        selected_table = st.sidebar.selectbox("Select Table", tables)
        display_table_explorer(conn, selected_table)
    
    elif app_mode == "Data Management":
        selected_table = st.sidebar.selectbox("Select Table", tables)
        management_action = st.sidebar.radio(
            "Choose Action",
            ["View Records", "Add Record", "Edit Record", "Delete Record"]
        )
        
        if management_action == "View Records":
            display_view_records(conn, selected_table)
        elif management_action == "Add Record":
            display_add_record(conn, selected_table)
        elif management_action == "Edit Record":
            display_edit_record(conn, selected_table)
        elif management_action == "Delete Record":
            display_delete_record(conn, selected_table)
    
    # Footer
    st.markdown("""
    <div class="footer">
        PostgreSQL Database Dashboard • Created with Streamlit
    </div>
    """, unsafe_allow_html=True)

def display_dashboard(conn, tables):
    st.markdown("<h1 class='main-header'>PostgreSQL Database Dashboard</h1>", unsafe_allow_html=True)
    
    metrics = generate_metrics(conn, tables)
    
    # Dashboard layout with columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        st.metric("Total Tables", metrics['total_tables'])
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        st.metric("Total Records", metrics['total_records'])
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        if metrics['latest_date']:
            st.metric("Latest Record", metrics['latest_date'].strftime("%Y-%m-%d %H:%M"))
        else:
            st.metric("Latest Record", "N/A")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Table metrics
    st.markdown("<h2 class='sub-header'>Table Statistics</h2>", unsafe_allow_html=True)
    
    # Create a dataframe of table metrics
    table_metrics = []
    for table in tables:
        count = get_table_count(conn, table)
        table_metrics.append({
            'Table': table,
            'Records': count
        })
    
    table_df = pd.DataFrame(table_metrics)
    
    # Show table metrics chart
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Bar chart of record counts
        if not table_df.empty:
            table_df = table_df.sort_values('Records', ascending=False)
            fig = px.bar(
                table_df, 
                x='Table', 
                y='Records',
                title='Records per Table',
                labels={'Records': 'Number of Records', 'Table': 'Table Name'},
                color='Records',
                color_continuous_scale='Blues'
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Table of record counts
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Table Records")
        st.dataframe(table_df, hide_index=True, height=350)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Time series data if available
    if metrics['time_series_data'] is not None:
        st.markdown("<h2 class='sub-header'>User Growth Over Time</h2>", unsafe_allow_html=True)
        
        fig = px.line(
            metrics['time_series_data'], 
            x='month', 
            y='count',
            markers=True,
            labels={'count': 'New Users', 'month': 'Month'},
            title='User Growth by Month'
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Database connection info
    st.markdown("<h2 class='sub-header'>Database Connection</h2>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    
    connection_params = conn.get_dsn_parameters()
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Host:** {connection_params['host']}")
        st.markdown(f"**Database:** {connection_params['dbname']}")
    
    with col2:
        st.markdown(f"**User:** {connection_params['user']}")
        st.markdown(f"**Port:** {connection_params['port']}")
    
    st.markdown("</div>", unsafe_allow_html=True)

def display_table_explorer(conn, selected_table):
    st.markdown(f"<h1 class='main-header'>Table Explorer: {selected_table}</h1>", unsafe_allow_html=True)
    
    # Get table schema
    schema = get_table_schema(conn, selected_table)
    
    # Get primary key
    primary_key = get_primary_key(conn, selected_table)
    
    # Get foreign keys
    foreign_keys = get_foreign_keys(conn, selected_table)
    
    # Show table structure
    st.markdown("<h2 class='sub-header'>Table Structure</h2>", unsafe_allow_html=True)
    
    # Create a DataFrame for the schema
    schema_df = pd.DataFrame(
        schema, 
        columns=['Column Name', 'Data Type', 'Nullable', 'Default', 'Max Length']
    )
    
    # Add primary key and foreign key information
    pk_col = []
    fk_col = []
    
    for col in schema_df['Column Name']:
        pk_col.append('✓' if col == primary_key else '')
        fk_col.append('✓' if col in foreign_keys else '')
    
    schema_df['Primary Key'] = pk_col
    schema_df['Foreign Key'] = fk_col
    
    # Display the schema
    st.markdown("<div class='table-container'>", unsafe_allow_html=True)
    st.dataframe(schema_df, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Display foreign key relationships
    if foreign_keys:
        st.markdown("<h3>Foreign Key Relationships</h3>", unsafe_allow_html=True)
        
        fk_data = []
        for col, (ref_table, ref_col) in foreign_keys.items():
            fk_data.append({
                'Column': col,
                'References Table': ref_table,
                'References Column': ref_col
            })
        
        fk_df = pd.DataFrame(fk_data)
        st.markdown("<div class='table-container'>", unsafe_allow_html=True)
        st.dataframe(fk_df, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Show sample data
    st.markdown("<h2 class='sub-header'>Sample Data</h2>", unsafe_allow_html=True)
    
    # Get sample data (10 rows)
    df = get_table_data(conn, selected_table, limit=10)
    
    if df.empty:
        st.info(f"No data available in {selected_table}")
    else:
        # Convert timestamp columns to a readable format
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        st.markdown("<div class='table-container'>", unsafe_allow_html=True)
        st.dataframe(df, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Export options
        st.markdown("<h3>Export Data</h3>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(export_table_to_csv(df), unsafe_allow_html=True)
        
        with col2:
            st.markdown(export_table_to_excel(df), unsafe_allow_html=True)
    
    # Table statistics
    st.markdown("<h2 class='sub-header'>Table Statistics</h2>", unsafe_allow_html=True)
    
    record_count = get_table_count(conn, selected_table)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        st.metric("Total Records", record_count)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
        st.metric("Columns", len(schema))
        st.markdown("</div>", unsafe_allow_html=True)

def display_view_records(conn, selected_table):
    st.markdown(f"<h1 class='main-header'>View Records: {selected_table}</h1>", unsafe_allow_html=True)
    
    # Filter options
    st.markdown("<h2 class='sub-header'>Filter Options</h2>", unsafe_allow_html=True)
    
    # Get table schema
    schema = get_table_schema(conn, selected_table)
    
    # Get primary key
    primary_key = get_primary_key(conn, selected_table)
    
    # Get foreign keys
    foreign_keys = get_foreign_keys(conn, selected_table)
    
    # Create filter UI
    filter_col = st.selectbox(
        "Filter by column", 
        [col[0] for col in schema],
        index=0 if schema else None
    )
    
    filter_value = None
    if filter_col:
        col_info = next((col for col in schema if col[0] == filter_col), None)
        
        if col_info:
            col_name, data_type, is_nullable, col_default, char_max_length = col_info
            
            # Check if it's a foreign key
            if filter_col in foreign_keys:
                foreign_table, foreign_column = foreign_keys[filter_col]
                options = get_foreign_key_options(conn, foreign_table, foreign_column)
                
                # Add empty option
                options[""] = "--- Select ---"
                
                filter_value = st.selectbox(
                    f"Select {filter_col}", 
                    options=list(options.keys()),
                    format_func=lambda x: options.get(x, x),
                    index=0
                )
            
            # Handle different data types
            elif data_type in ['integer', 'smallint', 'bigint']:
                filter_value = st.number_input(f"Enter {filter_col}", step=1)
            
            elif data_type in ['numeric', 'decimal', 'real', 'double precision']:
                filter_value = st.number_input(f"Enter {filter_col}", step=0.01, format="%.2f")
            
            elif data_type == 'boolean':
                filter_value = st.checkbox(f"Select {filter_col}")
            
            elif data_type == 'date':
                filter_value = st.date_input(f"Select {filter_col}")
                filter_value = filter_value.strftime('%Y-%m-%d')
            
            elif data_type in ['timestamp', 'timestamptz', 'timestamp with time zone', 'timestamp without time zone']:
                filter_date = st.date_input(f"Select {filter_col} (date)")
                filter_value = filter_date.strftime('%Y-%m-%d')
            
            else:  # Default to text input for other types
                filter_value = st.text_input(f"Enter {filter_col}")
    
    # Apply button
    filter_clause = None
    col1, col2 = st.columns([1, 3])
    
    with col1:
        apply_filter = st.button("Apply Filter")
    
    with col2:
        clear_filter = st.button("Clear Filter")
    
    # Reset filter if clear button clicked
    if clear_filter:
        filter_clause = None
    
    # Construct filter clause if button clicked
    if apply_filter and filter_col and filter_value not in [None, '']:
        col_info = next((col for col in schema if col[0] == filter_col), None)
        data_type = col_info[1] if col_info else None
        
        if data_type in ['varchar', 'text', 'char', 'character varying']:
            filter_clause = f"{filter_col} ILIKE '%{filter_value}%'"
        elif data_type in ['timestamp', 'timestamptz', 'timestamp with time zone', 'timestamp without time zone', 'date']:
            filter_clause = f"{filter_col}::date = '{filter_value}'::date"
        else:
            filter_clause = f"{filter_col} = '{filter_value}'"
    
    # Record limit
    st.markdown("<h2 class='sub-header'>Records</h2>", unsafe_allow_html=True)
    limit = st.slider("Number of records to display", min_value=10, max_value=1000, value=100, step=10)
    
    # Get table data
    df = get_table_data(conn, selected_table, limit=limit, where_clause=filter_clause)
    
    if df.empty:
        st.info(f"No data available in {selected_table}" + (" with the selected filter" if filter_clause else ""))
    else:
        # Convert timestamp columns to a readable format
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Display data
        st.markdown("<div class='table-container'>", unsafe_allow_html=True)
        st.dataframe(df, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Show record count
        st.markdown(f"<p>Showing {len(df)} records</p>", unsafe_allow_html=True)
        
        # Export options
        st.markdown("<h3>Export Options</h3>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(export_table_to_csv(df), unsafe_allow_html=True)
        
        with col2:
            st.markdown(export_table_to_excel(df), unsafe_allow_html=True)

def display_add_record(conn, selected_table):
    st.markdown(f"<h1 class='main-header'>Add Record: {selected_table}</h1>", unsafe_allow_html=True)
    
    # Get table schema
    schema = get_table_schema(conn, selected_table)
    
    # Get foreign keys
    foreign_keys = get_foreign_keys(conn, selected_table)
    
    # Form
    st.markdown("<h2 class='sub-header'>New Record</h2>", unsafe_allow_html=True)
    
    # Create a form for adding a record
    with st.form(key=f"add_record_form_{selected_table}"):
        values = {}
        
        for col in schema:
            col_name, data_type, is_nullable, col_default, char_max_length = col
            
            # Skip auto-increment columns
            if col_default and 'nextval' in str(col_default):
                continue
                
            # Generate form input
            value = generate_form_input(col_name, data_type, is_nullable, col_default, char_max_length, foreign_keys, conn)
            
            if value is not None:  # Only add non-None values
                values[col_name] = value
        
        # Submit button
        submit_button = st.form_submit_button(label="Add Record")
    
    # Handle form submission
    if submit_button:
        # Validate data
        errors = validate_data(values, schema, foreign_keys)
        
        if errors:
            for error in errors:
                st.error(error)
        else:
            # Insert record
            success, result = insert_record(conn, selected_table, values)
            
            if success:
                st.markdown("<div class='success-message'>Record added successfully!</div>", unsafe_allow_html=True)
                # Show the inserted ID if available
                st.markdown(f"<p>New record ID: <span class='highlight'>{result}</span></p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='error-message'>Error adding record: {result}</div>", unsafe_allow_html=True)

def display_edit_record(conn, selected_table):
    st.markdown(f"<h1 class='main-header'>Edit Record: {selected_table}</h1>", unsafe_allow_html=True)
    
    # Get primary key
    primary_key = get_primary_key(conn, selected_table)
    
    if not primary_key:
        st.error(f"No primary key found for table {selected_table}. Cannot edit records.")
        return
    
    # Get all records for selection
    records_df = get_table_data(conn, selected_table)
    
    if records_df.empty:
        st.info(f"No records available in {selected_table}")
        return
    
    # Get table schema
    schema = get_table_schema(conn, selected_table)
    
    # Get foreign keys
    foreign_keys = get_foreign_keys(conn, selected_table)
    
    # Select record to edit
    st.markdown("<h2 class='sub-header'>Select Record</h2>", unsafe_allow_html=True)
    
    # Try to find a descriptive column (name, title, etc.)
    descriptive_cols = [col for col in records_df.columns if any(s in col.lower() for s in ['name', 'title', 'description', 'email'])]
    display_col = descriptive_cols[0] if descriptive_cols else None
    
    # Format options for selectbox
    options = {}
    for _, row in records_df.iterrows():
        pk_value = row[primary_key]
        if display_col:
            display_value = f"{pk_value} - {row[display_col]}"
        else:
            display_value = str(pk_value)
        options[str(pk_value)] = display_value
    
    selected_pk = st.selectbox(
        f"Select record by {primary_key}",
        options=list(options.keys()),
        format_func=lambda x: options.get(x, x)
    )
    
    # Get the selected record
    selected_record = records_df[records_df[primary_key] == int(selected_pk) if selected_pk.isdigit() else selected_pk].iloc[0]
    
    # Form for editing
    st.markdown("<h2 class='sub-header'>Edit Record</h2>", unsafe_allow_html=True)
    
    with st.form(key=f"edit_record_form_{selected_table}_{selected_pk}"):
        values = {}
        
        for col in schema:
            col_name, data_type, is_nullable, col_default, char_max_length = col
            
            # Skip primary key
            if col_name == primary_key:
                continue
                
            # Generate form input with existing value
            existing_value = selected_record[col_name] if col_name in selected_record else None
            value = generate_form_input(col_name, data_type, is_nullable, col_default, char_max_length, foreign_keys, conn, existing_value)
            
            if value is not None:  # Only add non-None values
                values[col_name] = value
        
        # Submit button
        submit_button = st.form_submit_button(label="Update Record")
    
    # Handle form submission
    if submit_button:
        # Validate data
        errors = validate_data(values, schema, foreign_keys)
        
        if errors:
            for error in errors:
                st.error(error)
        else:
            # Update record
            success, message = update_record(conn, selected_table, selected_pk, primary_key, values)
            
            if success:
                st.markdown("<div class='success-message'>Record updated successfully!</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='error-message'>Error updating record: {message}</div>", unsafe_allow_html=True)

def display_delete_record(conn, selected_table):
    st.markdown(f"<h1 class='main-header'>Delete Record: {selected_table}</h1>", unsafe_allow_html=True)
    
    # Get primary key
    primary_key = get_primary_key(conn, selected_table)
    
    if not primary_key:
        st.error(f"No primary key found for table {selected_table}. Cannot delete records.")
        return
    
    # Get all records for selection
    records_df = get_table_data(conn, selected_table)
    
    if records_df.empty:
        st.info(f"No records available in {selected_table}")
        return
    
    # Select record to delete
    st.markdown("<h2 class='sub-header'>Select Record</h2>", unsafe_allow_html=True)
    
    # Try to find a descriptive column (name, title, etc.)
    descriptive_cols = [col for col in records_df.columns if any(s in col.lower() for s in ['name', 'title', 'description', 'email'])]
    display_col = descriptive_cols[0] if descriptive_cols else None
    
    # Format options for selectbox
    options = {}
    for _, row in records_df.iterrows():
        pk_value = row[primary_key]
        if display_col:
            display_value = f"{pk_value} - {row[display_col]}"
        else:
            display_value = str(pk_value)
        options[str(pk_value)] = display_value
    
    selected_pk = st.selectbox(
        f"Select record by {primary_key}",
        options=list(options.keys()),
        format_func=lambda x: options.get(x, x)
    )
    
    # Get the selected record
    selected_record = records_df[records_df[primary_key] == int(selected_pk) if selected_pk.isdigit() else selected_pk].iloc[0]
    
    # Display record details
    st.markdown("<h2 class='sub-header'>Record Details</h2>", unsafe_allow_html=True)
    
    # Format the record as a readable table
    record_details = {}
    for col in selected_record.index:
        value = selected_record[col]
        if pd.isna(value):
            value = "NULL"
        elif isinstance(value, (datetime, pd.Timestamp)):
            value = value.strftime('%Y-%m-%d %H:%M:%S')
        record_details[col] = [value]
    
    details_df = pd.DataFrame(record_details).T.reset_index()
    details_df.columns = ['Column', 'Value']
    
    st.markdown("<div class='table-container'>", unsafe_allow_html=True)
    st.dataframe(details_df, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Delete confirmation
    st.markdown("<h2 class='sub-header'>Confirmation</h2>", unsafe_allow_html=True)
    st.warning(f"Are you sure you want to delete this record from {selected_table}? This action cannot be undone.")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        delete_button = st.markdown("<div class='delete-button'>", unsafe_allow_html=True)
        delete_confirmed = st.button("Delete Record")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.button("Cancel")
    
    # Handle delete confirmation
    if delete_confirmed:
        success, message = delete_record(conn, selected_table, selected_pk, primary_key)
        
        if success:
            st.markdown("<div class='success-message'>Record deleted successfully!</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='error-message'>Error deleting record: {message}</div>", unsafe_allow_html=True)

# Run the application
if __name__ == "__main__":
    main()