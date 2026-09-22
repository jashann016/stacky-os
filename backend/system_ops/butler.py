import os
import shutil
from pathlib import Path
from typing import Dict, Any, List

class DesktopButler:
    """Intelligently classifies and organizes files into structured folders."""
    
    FOLDER_MAP = {
        "Invoices_and_Finance": [".pdf", ".csv", ".xlsx"],
        "Media_and_Graphics": [".png", ".jpg", ".jpeg", ".svg", ".mov", ".mp4"],
        "Code_and_Development": [".py", ".js", ".ts", ".html", ".css", ".json", ".zip", ".tar.gz"],
        "Documents_and_Notes": [".docx", ".txt", ".md", ".pages"]
    }

    @classmethod
    def sweep_and_organize_directory(cls, target_dir: str = None) -> Dict[str, Any]:
        if not target_dir:
            # Safe default: sandbox downloads or test workspace
            target_dir = str(Path(__file__).resolve().parent.parent.parent / "sandbox_inbox")
        
        path = Path(target_dir)
        path.mkdir(exist_ok=True)

        moved_files = []
        for file in path.iterdir():
            if file.is_file() and not file.name.startswith("."):
                ext = file.suffix.lower()
                dest_folder_name = "General_Archive"
                
                for folder, extensions in cls.FOLDER_MAP.items():
                    if ext in extensions:
                        dest_folder_name = folder
                        break

                dest_dir = path / dest_folder_name
                dest_dir.mkdir(exist_ok=True)
                
                dest_file = dest_dir / file.name
                if not dest_file.exists():
                    try:
                        shutil.move(str(file), str(dest_file))
                        moved_files.append({"file": file.name, "category": dest_folder_name})
                    except Exception:
                        pass

        return {
            "status": "COMPLETED",
            "target_directory": str(path),
            "files_organized_count": len(moved_files),
            "organized_manifest": moved_files[:8]
        }
