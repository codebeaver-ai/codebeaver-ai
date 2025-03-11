from pathlib import Path
import logging

logger = logging.getLogger("codebeaver")


class GitUtils:
    """
    This class handles anything related to committing/pushing new code.
    """

    def __init__(self):
        pass

    @staticmethod
    def ensure_codebeaver_folder_exists_and_in_gitignore():
        """
        Ensure the .codebeaver/ folder exists and is in .gitignore at the project root.

        Creates the .codebeaver/ directory if it doesn't exist and ensures it's listed
        in .gitignore at the project root.

        Returns:
            bool: True if any changes were made (dir created or .gitignore updated),
                  False if everything was already set up.
        """

        # Find the project root (where setup.py or pyproject.toml is)
        current_dir = Path.cwd()
        root_markers = ["setup.py", "pyproject.toml"]

        while current_dir != current_dir.parent:
            if any((current_dir / marker).exists() for marker in root_markers):
                break
            current_dir = current_dir.parent

        gitignore_path = current_dir / ".gitignore"
        entry_to_add = ".codebeaver/"

        # Create .codebeaver directory if it doesn't exist
        codebeaver_dir = current_dir / ".codebeaver"
        dir_created = False
        if not codebeaver_dir.exists():
            codebeaver_dir.mkdir()
            logger.debug(f"Created '{entry_to_add}' directory")
            dir_created = True

        try:
            # Check if .gitignore exists
            try:
                with open(gitignore_path, "r") as f:
                    content = f.read().splitlines()
            except FileNotFoundError:
                content = []

            # Check if .codebeaver/ is already in the file (with variations)
            normalized_entry = entry_to_add.strip("/")
            for line in content:
                line = line.strip()
                if line and not line.startswith("#"):
                    if normalized_entry == line.strip("/"):
                        logger.debug(f"'{entry_to_add}' is already in .gitignore")
                        return False or dir_created

            # Add .codebeaver/ to .gitignore
            with open(gitignore_path, "a") as f:
                if content and content[-1] != "":
                    f.write("\n")

                f.write(f"# CodeBeaver reports and artifacts\n{entry_to_add}\n")

            logger.info(f"Added '{entry_to_add}' to .gitignore")
            return True or dir_created

        except Exception as e:
            logger.error(f"Error updating .gitignore: {e}")
            return dir_created  # Return True if at least the directory was created
