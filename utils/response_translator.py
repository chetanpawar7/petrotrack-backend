def success_response(data, message, total_count=None):
    """
    Returns a success response with the given data and message.
    """
    response = {
        "status": "success",
        "message": message,
        "data": data
    }
    if total_count:
        response["total_count"] = total_count
    return response

def error_response(message):
    """
    Returns an error response with the given message.
    """
    response = {
        "status": "error",
        "message": message
    }
    return response
