"""Tests for config module."""

import os
import tempfile
import shutil
from pathlib import Path

import pytest


@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for config testing."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    yield temp_dir
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestConfig:
    """Tests for config module functions."""

    def test_load_config_not_exists(self, temp_config_dir):
        """Test loading config when file doesn't exist."""
        # Need to reload the module to pick up new directory
        import importlib
        import mentis.config

        importlib.reload(mentis.config)

        result = mentis.config.load_config()
        assert result == {}

    def test_save_and_load_config(self, temp_config_dir):
        """Test saving and loading config."""
        import importlib
        import mentis.config

        importlib.reload(mentis.config)

        config = {"model": "llama3.2", "username": "Alice"}
        mentis.config.save_config(config)

        result = mentis.config.load_config()
        assert result == config

    def test_get_set_model(self, temp_config_dir):
        """Test getting and setting model."""
        import importlib
        import mentis.config

        importlib.reload(mentis.config)

        user = "bob"

        mentis.config.set_model(user, "mistral")
        result = mentis.config.get_model(user)
        assert result == "mistral"

    def test_get_set_username(self, temp_config_dir):
        """Test getting and setting username."""
        import importlib
        import mentis.config

        importlib.reload(mentis.config)

        mentis.config.set_username("Bob")
        result = mentis.config.get_username()
        assert result == "Bob"

    def test_get_config_default(self, temp_config_dir):
        """Test get_config with default value."""
        import importlib
        import mentis.config

        importlib.reload(mentis.config)

        result = mentis.config.get_config("nonexistent", "default_value")
        assert result == "default_value"

    def test_find_existing_usernames_from_files(self, temp_config_dir):
        """Test finding usernames from KG files."""
        import importlib
        import mentis.config

        importlib.reload(mentis.config)

        # Create mock KG files
        Path("kg_Alice.graphml").write_text("")
        Path("kg_Bob.ttl").write_text("")
        Path("kg_Charlie.graphml").write_text("")
        # Also create a non-KG file that shouldn't be matched
        Path("kg_backup.graphml.bak").write_text("")

        result = mentis.config.find_existing_usernames()
        assert "Alice" in result
        assert "Bob" in result
        assert "Charlie" in result
        # Should not include backup file
        assert "kg_backup.graphml.bak" not in result

    def test_add_known_username(self, temp_config_dir):
        """Test adding a known username."""
        import importlib
        import mentis.config

        importlib.reload(mentis.config)

        mentis.config.add_known_username("Alice")
        mentis.config.add_known_username("Bob")
        mentis.config.add_known_username("Alice")  # Duplicate

        config = mentis.config.load_config()
        assert "usernames" in config
        assert "Alice" in config["usernames"]
        assert "Bob" in config["usernames"]
        assert config["usernames"].count("Alice") == 1  # No duplicates
