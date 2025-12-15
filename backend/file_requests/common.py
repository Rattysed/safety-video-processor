ALLOWED_FILE_EXTENSIONS = [".mp4", ".mkv", ".mov", ".avi"]

def validate_file_extensions(extensions_list: list[str], filename: str) -> bool:
    for extension in extensions_list:
        if filename.endswith(extension):
            return True
    return False
