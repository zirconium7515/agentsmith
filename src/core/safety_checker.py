import os

WARNING_EXTENSIONS = {
    ".pt", ".pth", ".h5", ".hdf5", ".bin", ".ckpt",  # Model weights
    ".mp4", ".avi", ".mkv", ".mov",                  # Video
    ".jpg", ".jpeg", ".png", ".bmp", ".tiff",        # Image datasets
    ".db", ".sqlite", ".sqlite3",                    # Databases
    ".csv", ".tsv", ".txt"                           # Potential raw data
}

def check_large_file(filepath: str, max_size_mb: int = 5) -> bool:
    """Returns True if file is larger than max_size_mb."""
    try:
        size_bytes = os.path.getsize(filepath)
        return size_bytes > (max_size_mb * 1024 * 1024)
    except OSError:
        return False

def get_warnings_for_inclusion(filepath: str) -> list[str]:
    """Returns a list of warning messages if the file shouldn't be blindly included."""
    warnings = []
    
    # 1. Large file check
    if check_large_file(filepath, 10):
        warnings.append(f"Large file detected (>10MB): {os.path.basename(filepath)}")
        
    # 2. Extension check
    _, ext = os.path.splitext(filepath)
    if ext.lower() in WARNING_EXTENSIONS:
        warnings.append(f"Potentially sensitive/binary extension ({ext}): {os.path.basename(filepath)}")
        
    # 3. GD sync conflict check (typical Google Drive conflict pattern)
    if " (1)" in filepath or " (2)" in filepath or "conflict" in filepath.lower():
        warnings.append(f"Potential Google Drive sync conflict file: {os.path.basename(filepath)}")
        
    return warnings
