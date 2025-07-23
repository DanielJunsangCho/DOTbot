import csv
from langchain_core.tools import tool

@tool
def write_to_csv(data: list, filename: str = "output.csv") -> bool:
    """
    Writes a list of dictionaries to a CSV file.
    Args:
        data: List of dictionaries, where each dict represents a row.
        filename: Name of the CSV file to write to.
    Returns:
        True if successful, False otherwise.
    """
    if not data:
        return False
    try:
        # Get the fieldnames from the first dict
        fieldnames = data[0].keys()
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        return True
    except Exception as e:
        print(f"Error writing CSV: {e}")
        return False

