def load_logfile(file_storage):
    """Read uploaded file from Flask request.files and return UTF-8 text."""
    # file_storage is a Werkzeug FileStorage
    content = file_storage.read()
    try:
        return content.decode('utf-8', errors='ignore')
    except AttributeError:
        # Already a str
        return content
