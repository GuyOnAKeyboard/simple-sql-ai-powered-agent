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

tool_kit=[load_csv_file, kaggle_dataset_tool, explore_temp_csv, find_file_path]