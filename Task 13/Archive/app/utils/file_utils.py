def allowed_file(filename, allowed_extensions):
    if "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in allowed_extensions


def safe_filename(file_name):
    invalid = '<>:"/\\|?*\n\r\t'
    output = "".join("_" if ch in invalid else ch for ch in file_name).strip(" .")
    return output or "uploaded_file"


def ensure_suffix(file_path, suffix):
    if file_path.suffix.lower() == suffix.lower():
        return file_path
    return file_path.with_suffix(suffix)
