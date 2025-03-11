import os
import pytest
import logging
from pathlib import Path
from src.codebeaver.GitUtils import GitUtils

class TestGitUtils:
    """Test suite for GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore()"""

    @pytest.fixture
    def project_root(self, tmp_path):
        """
        Creates a temporary project structure with a project root containing a 'setup.py' marker.
        Returns the project root Path.
        """
        project = tmp_path / "project"
        project.mkdir()
        # Create a marker file
        (project / "setup.py").write_text("# dummy setup")
        return project

    @pytest.fixture
    def change_to_subdir(self, project_root, monkeypatch):
        """
        Change current working directory to a subdirectory inside the project root.
        Returns the subdirectory Path.
        """
        subdir = project_root / "sub"
        subdir.mkdir()
        monkeypatch.chdir(subdir)
        return subdir

    def test_creates_dir_and_gitignore(self, project_root, change_to_subdir):
        """
        Test that when neither '.codebeaver' folder nor '.gitignore' exists,
        they are created and updated correctly.
        """
        ret = GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore()
        # The function should return True since at least the file .gitignore is updated.
        assert ret is True

        # Check '.codebeaver' directory exists at project root.
        codeb_dir = project_root / ".codebeaver"
        assert codeb_dir.is_dir()

        # Check '.gitignore' exists and contains the required entry.
        gitignore_path = project_root / ".gitignore"
        assert gitignore_path.is_file()
        content = gitignore_path.read_text()
        assert "# CodeBeaver reports and artifacts" in content
        assert ".codebeaver/" in content

    def test_no_changes_when_already_set_up(self, project_root, change_to_subdir):
        """
        Test that if '.codebeaver' folder exists and '.gitignore' already contains the entry,
        the function makes no changes and returns False.
        """
        # Pre-create '.codebeaver' directory at the project root.
        codeb_dir = project_root / ".codebeaver"
        codeb_dir.mkdir()

        # Pre-create .gitignore with the correct entry.
        gitignore_path = project_root / ".gitignore"
        content = "# CodeBeaver reports and artifacts\n.codebeaver/\n"
        gitignore_path.write_text(content)

        ret = GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore()
        # Since both exist, the function should return False.
        # (Note: if the directory had been created in this run, it would return True, but here it hasn't.)
        assert ret is False

    def test_appends_entry_to_gitignore_when_missing(self, project_root, change_to_subdir):
        """
        Test that if '.gitignore' exists without the '.codebeaver/' entry,
        the entry is appended correctly (with a preceding newline if needed).
        """
        # Pre-create '.codebeaver' directory.
        codeb_dir = project_root / ".codebeaver"
        codeb_dir.mkdir()

        # Pre-create a .gitignore that does not have the '.codebeaver/' entry and does not end with a newline.
        gitignore_path = project_root / ".gitignore"
        initial_content = "existing_entry"
        gitignore_path.write_text(initial_content)

        ret = GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore()
        # The function should append entry so return True.
        assert ret is True

        updated_content = gitignore_path.read_text()
        # Check that a newline was added before appending the CodeBeaver section.
        assert "existing_entry\n" in updated_content
        assert "# CodeBeaver reports and artifacts" in updated_content
        assert ".codebeaver/" in updated_content

    def test_exception_handling_in_gitignore_update(self, project_root, change_to_subdir, monkeypatch, caplog):
        """
        Test that when an exception occurs during .gitignore update (e.g., failure when opening for append),
        the function logs an error and returns dir_created status.
        """
        # Ensure .codebeaver does not exist initially, so the function will attempt to create it.
        codeb_dir = project_root / ".codebeaver"
        if codeb_dir.exists():
            os.rmdir(codeb_dir)

        # Create a dummy open function that raises an exception when mode is 'a'
        orig_open = open
        def fake_open(*args, **kwargs):
            mode = kwargs.get("mode", args[1] if len(args)>=2 else "")
            if "a" in mode:
                raise Exception("Forced exception on write")
            return orig_open(*args, **kwargs)

        monkeypatch.setattr("builtins.open", fake_open)

        with caplog.at_level(logging.ERROR):
            ret = GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore()
            # Since directory was not present, it should now be created (dir_created=True).
            # And due to exception, the function returns dir_created (True).
            assert ret is True
            assert "Error updating .gitignore" in caplog.text

        # Verify that the .gitignore may not exist due to the exception
        gitignore_path = project_root / ".gitignore"
        # It might have been created but remains empty or not written properly.
        # So we don't enforce its content here.

    def test_appends_when_entry_is_commented(self, project_root, change_to_subdir):
        """
        Test that if the .gitignore file has a commented-out version of the entry,
        the function still appends the required entry.
        """
        # Pre-create '.codebeaver' directory.
        codeb_dir = project_root / ".codebeaver"
        codeb_dir.mkdir()

        # Create a .gitignore file with a commented line resembling the entry.
        gitignore_path = project_root / ".gitignore"
        content = "# .codebeaver/\nsome_other_line\n"
        gitignore_path.write_text(content)

        ret = GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore()
        # Even though there is a line mentioning '.codebeaver/', it is commented so
        # the function should append the proper entry and return True.
        assert ret is True

        updated_content = gitignore_path.read_text()
        assert "# CodeBeaver reports and artifacts" in updated_content
        assert ".codebeaver/" in updated_content

    def test_creates_dir_when_gitignore_has_entry(self, project_root, change_to_subdir):
        """Test that if .gitignore already contains the correct entry but the .codebeaver directory is missing,
        the directory is created and the function returns True."""
        gitignore_path = project_root / ".gitignore"
        content = "# CodeBeaver reports and artifacts\n.codebeaver/\n"
        gitignore_path.write_text(content)

        codeb_dir = project_root / ".codebeaver"
        assert not codeb_dir.exists()
        ret = GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore()
        # The .codebeaver directory was created, so even though the .gitignore already had the entry,
        # the function should return True because (False or True) evaluates to True.
        assert ret is True
        assert codeb_dir.is_dir()

    def test_exception_in_read_gitignore(self, project_root, change_to_subdir, monkeypatch, caplog):
        """Test that an exception during reading .gitignore is handled properly and returns directory created status."""
        orig_open = open
        def fake_open(*args, **kwargs):
            mode = kwargs.get("mode", args[1] if len(args) > 1 else "")
            if "r" in mode:
                raise Exception("Forced exception in read")
            return orig_open(*args, **kwargs)

        monkeypatch.setattr("builtins.open", fake_open)

        with caplog.at_level(logging.ERROR):
            codeb_dir = project_root / ".codebeaver"
            if codeb_dir.exists():
                codeb_dir.rmdir()
            ret = GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore()
            # The .codebeaver directory should have been created (so dir_created is True) even though reading .gitignore failed.
            assert ret is True
            assert "Error updating .gitignore" in caplog.text
            assert codeb_dir.is_dir()

    def test_no_marker_found(self, tmp_path, monkeypatch):
        """Test behavior when no setup.py or pyproject.toml marker is found.
        This test forces the current directory to be treated as the project root (by making its parent equal to itself),
        so that GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore() creates the .codebeaver folder and updates .gitignore.
        """
        # Force the tmp_path to appear as the root by monkeypatching its parent property.
        monkeypatch.setattr(type(tmp_path), "parent", property(lambda self: self))
        # Monkey-patch Path.cwd() so that the current working directory is tmp_path.
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path)
        
        ret = GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore()
        # Since .codebeaver is created and .gitignore updated, ret should be True.
        assert ret is True
        codeb_dir = tmp_path / ".codebeaver"
        assert codeb_dir.is_dir()
        gitignore_path = tmp_path / ".gitignore"
        assert gitignore_path.is_file()
        content = gitignore_path.read_text()
        assert "# CodeBeaver reports and artifacts" in content
        assert ".codebeaver/" in content

    def test_with_pyproject_marker(self, project_root, change_to_subdir):
        """Test that a pyproject.toml marker (instead of setup.py) is correctly detected as the project root.
        The test removes setup.py in favor of creating pyproject.toml and then ensures that the .codebeaver folder
        is created and .gitignore is updated in that project root.
        """
        # Remove setup.py and create pyproject.toml marker in project_root.
        setup_py = project_root / "setup.py"
        if setup_py.exists():
            setup_py.unlink()
        (project_root / "pyproject.toml").write_text("[tool.poetry]\nname = 'dummy'")
        
        ret = GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore()
        # Expect True because .gitignore should be updated.
        assert ret is True
        codeb_dir = project_root / ".codebeaver"
        assert codeb_dir.is_dir()
        gitignore_path = project_root / ".gitignore"
        assert gitignore_path.is_file()
        content = gitignore_path.read_text()
        assert "# CodeBeaver reports and artifacts" in content
        assert ".codebeaver/" in content
    def test_mkdir_failure(self, project_root, change_to_subdir, monkeypatch):
        """Test that an OSError during directory creation (mkdir) is propagated."""
        # Monkeypatch Path.mkdir to raise OSError when attempting to create .codebeaver directory
        monkeypatch.setattr(Path, "mkdir", lambda self, *args, **kwargs: (_ for _ in ()).throw(OSError("Forced mkdir failure")))
        with pytest.raises(OSError) as excinfo:
            GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore()
        assert "Forced mkdir failure" in str(excinfo.value)

    def test_gitignore_normalized_entry_detected(self, project_root, change_to_subdir):
        """Test that a variably formatted .codebeaver entry in .gitignore is detected and no duplicate entry is appended."""
        gitignore_path = project_root / ".gitignore"
        # Write a variably formatted entry with extra slashes
        gitignore_path.write_text("### Some comment\n///.codebeaver///\n")

        # Ensure .codebeaver directory does not exist
        codeb_dir = project_root / ".codebeaver"
        if codeb_dir.exists():
            # remove it if exists
            os.rmdir(codeb_dir)

        ret = GitUtils.ensure_codebeaver_folder_exists_and_in_gitignore()
        # Directory should be created, so ret is True since (False or True) => True
        assert ret is True
        # .codebeaver directory should now exist
        assert codeb_dir.is_dir()
        # .gitignore content should remain unchanged (no duplicate appended)
        content = gitignore_path.read_text()
        # Count occurrences of the normalized entry; there should be exactly one.
        occurrences = content.count(".codebeaver/")
        assert occurrences == 1