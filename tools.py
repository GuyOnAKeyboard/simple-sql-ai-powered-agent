from langchain_core.tools import tool

@tool
def kaggle_dataset_tool(dataset_url: str) -> dict:
    """
    Downloads a Kaggle dataset from a URL and stores it inside temp_csv/<dataset-name>.
    Returns status, path, and dataset name.
    """

    import os
    import subprocess
    import sys

    try:
        # Extract dataset id from URL
        if "kaggle.com/datasets/" not in dataset_url:
            return {
                "status": "error",
                "message": "Invalid Kaggle dataset URL"
            }

        dataset_id = dataset_url.split("kaggle.com/datasets/")[-1].strip("/")
        folder_name = dataset_id.split("/")[-1]

        # Build path
        base_dir = os.path.join(os.getcwd(), "temp_csv")
        target_dir = os.path.join(base_dir, folder_name)

        os.makedirs(target_dir, exist_ok=True)

        # Run kaggle CLI command
        subprocess.run([
            sys.executable,
            "-m",
            "kaggle",
            "datasets",
            "download",
            dataset_id,
            "-p",
            target_dir,
            "--unzip"
        ], check=True)

        return {
            "status": "success",
            "dataset": folder_name,
            "path": target_dir
        }

    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "message": "Kaggle download failed",
            "details": str(e)
        }

    except Exception as e:
        return {
            "status": "error",
            "message": "Unexpected error occurred",
            "details": str(e)
        }



@tool
def explore_temp_csv(base_path: str = "temp_csv") -> dict:
    """
    Scans temp_csv folder and returns all subfolders and files inside it.
    """

    import os

    try:
        if not os.path.exists(base_path):
            return {
                "status": "error",
                "message": f"{base_path} folder does not exist"
            }

        structure = {}

        for root, dirs, files in os.walk(base_path):
            rel_path = os.path.relpath(root, base_path)
            structure[rel_path] = {
                "folders": dirs,
                "files": files
            }

        return {
            "status": "success",
            "base_path": base_path,
            "structure": structure
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@tool
def load_csv_file(file_path: str, rows: int = 5) -> dict:
    """
    Loads a CSV file using pandas and returns preview + metadata.
    Accepts direct CSV paths or a directory path containing a CSV file.
    """
    import pandas as pd
    import os

    try:
        if not os.path.exists(file_path):
            return {
                "status": "error",
                "message": f"Path not found: {file_path}"
            }

        # Smart Fallback: If it's a folder, search for a CSV file inside it
        if os.path.isdir(file_path):
            csv_files = [f for f in os.listdir(file_path) if f.endswith('.csv')]
            if not csv_files:
                return {
                    "status": "error",
                    "message": f"Provided path is a directory, and no CSV files were found inside it: {file_path}"
                }
            # Target the first CSV file found inside the folder
            file_path = os.path.join(file_path, csv_files[0])

        if not file_path.endswith(".csv"):
            return {
                "status": "error",
                "message": f"Only CSV files are supported. Found target file: {os.path.basename(file_path)}"
            }

        df = pd.read_csv(file_path)

        return {
            "status": "success",
            "file_loaded": os.path.basename(file_path),
            "shape": df.shape,
            "columns": list(df.columns),
            "preview": df.head(rows).to_dict(orient="records")
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@tool
def find_file_path(filename: str = "", target_directory: str = "") -> dict:
    """
    Searches a directory tree for files matching a filename substring and returns absolute paths.
    
    Args:
        filename: Optional substring to search for (e.g. 'movies'). If blank, lists all files.
        target_directory: Optional specific directory path. Defaults to 'temp_csv' if it exists, 
                          otherwise defaults to the current working project directory.
    """
    import os

    # 1. Smart directory fallback logic
    if target_directory:
        search_dir = os.path.abspath(target_directory)
    else:
        # Check if the standard workspace folder exists
        temp_csv_path = os.path.join(os.getcwd(), "temp_csv")
        if os.path.exists(temp_csv_path):
            search_dir = temp_csv_path
        else:
            # Fallback entirely to the system current working directory
            search_dir = os.getcwd()
    
    if not os.path.exists(search_dir):
        return {
            "status": "error",
            "message": f"The target search directory '{search_dir}' does not exist."
        }

    matches = []
    target_clean = filename.lower().strip() if filename else ""

    # 2. Traverse the selected directory tree structure
    for root, _, files in os.walk(search_dir):
        # Prevent infinite loops or scanning python hidden virtual environment files
        if ".venv" in root or "__pycache__" in root or ".git" in root:
            continue
            
        for file in files:
            if not target_clean or (target_clean in file.lower()):
                full_path = os.path.abspath(os.path.join(root, file))
                matches.append({
                    "filename": file,
                    "absolute_path": full_path,
                    "relative_path": os.path.relpath(full_path, os.getcwd())
                })

    if not matches:
        return {
            "status": "success",
            "search_directory": search_dir,
            "message": f"No files found matching criteria inside: {search_dir}"
        }

    return {
        "status": "success",
        "search_directory": search_dir,
        "matches_found": len(matches),
        "results": matches
    }


@tool
def create_postgres_table_from_csv(
    csv_path: str,
    table_name: str
) -> dict:
    """
    Creates a PostgreSQL table immediately.

    This tool performs the action directly.
    It connects to PostgreSQL using configured environment variables
    and executes CREATE TABLE.

    Use this whenever the user asks to:
    - create a table
    - create a schema
    - prepare a database table
    - import a dataset into PostgreSQL

    Do not generate SQL manually if this tool is available.
    """

    import os
    import pandas as pd
    import psycopg2
    from dotenv import load_dotenv
    

    try:
        load_dotenv()
        
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )

        df = pd.read_csv(csv_path, nrows=100)

        columns = []

        for col, dtype in df.dtypes.items():

            if "int" in str(dtype):
                sql_type = "BIGINT"

            elif "float" in str(dtype):
                sql_type = "DOUBLE PRECISION"

            elif "bool" in str(dtype):
                sql_type = "BOOLEAN"

            else:
                sql_type = "TEXT"

            safe_col = (
                col.lower()
                .replace(" ", "_")
                .replace("-", "_")
            )

            columns.append(
                f'"{safe_col}" {sql_type}'
            )

        sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name}
        (
            {",".join(columns)}
        )
        """

        cur = conn.cursor()
        cur.execute(sql)

        conn.commit()

        cur.close()
        conn.close()

        return {
            "status": "success",
            "table": table_name,
            "columns": len(columns)
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@tool
def load_csv_to_postgres(csv_path: str, table_name: str) -> dict:
    """ Loads a CSV file into a PostgreSQL table. 
    This tool: - Reads a CSV file from the given file path 
    - Connects to PostgreSQL using environment variables 
    (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD) 
    - Inserts all rows into the specified table using pandas.to_sql 
    - Appends data if the table already exists Use this tool when: 
    - The user asks to load data into PostgreSQL 
    - The user wants to insert a CSV into a database 
    - The user says "store dataset in database" 
    - The user wants to import or upload data to Postgres IMPORTANT:
    - This tool performs the full ingestion automatically
    - Do NOT generate SQL manually when this tool is available 
    - Do NOT ask the user to write insert scripts 
    - This is the primary tool for CSV → PostgreSQL ingestion 
    """

    import os
    import pandas as pd
    import numpy as np
    from sqlalchemy import create_engine
    from dotenv import load_dotenv

    try:
        load_dotenv()

        df = pd.read_csv(csv_path, low_memory=False, on_bad_lines="skip")

        if any("Unnamed" in str(c) for c in df.columns):
            df = pd.read_csv(csv_path, header=None, on_bad_lines="skip")
            df.columns = [f"col_{i}" for i in range(df.shape[1])]

        df.columns = (
            df.columns.astype(str)
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
            .str.replace("-", "_")
        )

        df = df.drop_duplicates()

        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

        df = df.replace(r'^\s*-\s*.*$', np.nan, regex=True)

        bool_map = {
            "true": True, "false": False,
            "1": True, "0": False,
            "yes": True, "no": False,
            "t": True, "f": False
        }

        for col in df.columns:
            if df[col].dtype == "object":
                s = df[col].astype(str).str.lower().str.strip()
                if s.isin(bool_map.keys()).mean() > 0.6:
                    df[col] = s.map(bool_map)

        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = pd.to_numeric(df[col], errors="ignore")

        df = df.where(pd.notnull(df), None)

        engine = create_engine(
            f"postgresql+psycopg2://"
            f"{os.getenv('DB_USER')}:"
            f"{os.getenv('DB_PASSWORD')}@"
            f"{os.getenv('DB_HOST')}:"
            f"{os.getenv('DB_PORT')}/"
            f"{os.getenv('DB_NAME')}"
        )

        df.to_sql(
            table_name,
            engine,
            if_exists="append",
            index=False,
            chunksize=1000,
            method="multi"
        )

        return {
            "status": "success",
            "rows_inserted": len(df),
            "columns": list(df.columns),
            "table_name": table_name
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@tool
def find_csv_files() -> dict:
    """
    Find all CSV files available in the workspace.
    """

    import os

    csv_files = []

    for root, _, files in os.walk(os.getcwd()):

        if ".venv" in root:
            continue

        for file in files:

            if file.lower().endswith(".csv"):

                csv_files.append(
                    os.path.join(root, file)
                )

    return {
        "count": len(csv_files),
        "files": csv_files
    }

@tool
def run_postgres_query(query: str) -> dict:
    """
    Executes a SQL query on PostgreSQL and returns the result.

    This tool:
    - Connects to PostgreSQL using environment variables
      (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)
    - Executes the provided SQL query
    - Fetches and returns results for SELECT queries
    - Returns row count for non-SELECT queries

    Use this tool when:
    - The user asks to run a SQL query
    - The user wants to fetch data from PostgreSQL
    - The user asks for analysis or retrieval from a table

    IMPORTANT:
    - Do NOT construct SQL manually outside this tool when it is available
    - This tool is the primary interface for querying the database
    """

    import os
    import psycopg2
    from dotenv import load_dotenv

    try:
        load_dotenv()

        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )

        cur = conn.cursor()
        cur.execute(query)

        # If it's a SELECT query, fetch results
        if cur.description is not None:
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

            result = [
                dict(zip(columns, row))
                for row in rows
            ]

            output = {
                "status": "success",
                "type": "select",
                "row_count": len(result),
                "data": result
            }
        else:
            conn.commit()
            output = {
                "status": "success",
                "type": "command",
                "rows_affected": cur.rowcount
            }

        cur.close()
        conn.close()

        return output

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@tool
def list_postgres_tables() -> dict:
    """
    Lists all tables in the connected PostgreSQL database.

    This tool:
    - Connects to PostgreSQL using environment variables
      (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)
    - Queries information_schema to fetch all user tables
    - Returns a list of table names

    Use this when:
    - User asks "how many tables are in my database"
    - User wants to see available tables
    - User asks for database schema overview
    """

    import os
    import psycopg2
    from dotenv import load_dotenv

    try:
        load_dotenv()

        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )

        cur = conn.cursor()

        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)

        tables = [row[0] for row in cur.fetchall()]

        cur.close()
        conn.close()

        return {
            "status": "success",
            "table_count": len(tables),
            "tables": tables
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
tool_kit=[load_csv_file, kaggle_dataset_tool, 
          explore_temp_csv, find_file_path,
          create_postgres_table_from_csv,load_csv_to_postgres,
          find_csv_files, run_postgres_query, list_postgres_tables]