import re

def get_username_from_email(email):
    """
    Extracts the username from the given email address.
    
    Args:
        email (str): The email address from which to extract the username.
        
    Returns:
        str: The extracted username, or None if the email format is invalid.
    """
    try:
        # Use regex to match the part before '@' in the email
        match = re.match(r"([^@]+)@", email)
        if match:
            return match.group(1)
        else:
            return None
    except Exception as e:
        return None