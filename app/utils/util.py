import re


def sanitize_json_string(json_string):
    """Removes unescaped control characters and escapes carriage returns,
    newlines, and tabs in the JSON string."""
    # Replace unescaped control characters (e.g., tabs, newlines)
    sanitized = re.sub(r'[\x00-\x1f\x7f]', '', json_string)

    # Replace any remaining problematic characters or escape sequences
    sanitized = sanitized.replace('\r', '\\r').replace('\n', '\\n').replace(
        '\t', '\\t')
    return sanitized


def convert_timestamp_to_timestamp_tz(store_procedure: str) -> str:
    """
    Convert TIMESTAMP to TIMESTAMP_TZ in the SQL stored procedure string.

    :param store_procedure: SQL stored procedure string.
    :return: Modified SQL stored procedure string with TIMESTAMP replaced by TIMESTAMP_TZ.
    """
    # Regular expression to find TIMESTAMP type declarations
    # This assumes TIMESTAMP is followed by optional precision and scale
    pattern = r'\bTIMESTAMP\_?(?:NTZ|LTZ|TZ)?\b'

    # Replace TIMESTAMP with TIMESTAMP_TZ
    modified_procedure = re.sub(pattern, '8', store_procedure)

    return modified_procedure
