"""Tests for CLI module."""

from unittest.mock import patch, MagicMock

from mentis.cli import main, prompt_model_choice, prompt_username


class TestPromptModelChoice:
    """Tests for prompt_model_choice function."""

    @patch("ollama.list")
    def test_list_models_with_models(self, mock_list):
        """Test listing models when models are available."""
        # Mock response with models
        mock_model = MagicMock()
        mock_model.model = "llama3.2"
        mock_model.size = 4700000000
        mock_list.return_value = MagicMock(models=[mock_model])

        result = prompt_model_choice()
        assert result == "llama3.2"

    @patch("ollama.list")
    def test_list_models_empty(self, mock_list):
        """Test listing models when no models available."""
        mock_list.return_value = MagicMock(models=[])

        result = prompt_model_choice()
        assert result == "llama3.2"  # Default fallback

    @patch("ollama.list")
    def test_list_models_exception(self, mock_list):
        """Test listing models when exception occurs."""
        mock_list.side_effect = Exception("Connection error")

        result = prompt_model_choice()
        assert result == "llama3.2"  # Default fallback

    @patch("ollama.list")
    def test_list_models_user_selection(self, mock_list):
        """Test user selecting a model."""
        mock_model1 = MagicMock()
        mock_model1.model = "llama3.2"
        mock_model1.size = 4700000000
        mock_model2 = MagicMock()
        mock_model2.model = "mistral"
        mock_model2.size = 3800000000
        mock_list.return_value = MagicMock(models=[mock_model1, mock_model2])

        with patch("builtins.input", side_effect=["2"]):
            result = prompt_model_choice()
            assert result == "mistral"

    @patch("ollama.list")
    def test_list_models_default_selection(self, mock_list):
        """Test default selection (empty input)."""
        mock_model = MagicMock()
        mock_model.model = "llama3.2"
        mock_list.return_value = MagicMock(models=[mock_model])

        with patch("builtins.input", side_effect=[""]):
            result = prompt_model_choice()
            assert result == "llama3.2"


class TestPromptUsername:
    """Tests for prompt_username function."""

    @patch("mentis.cli.find_existing_usernames")
    def test_prompt_username_valid(self, mock_find):
        """Test getting a valid username."""
        mock_find.return_value = []
        with patch("builtins.input", side_effect=["Alice"]):
            result = prompt_username()
            assert result == "Alice"

    @patch("mentis.cli.find_existing_usernames")
    def test_prompt_username_empty_then_valid(self, mock_find):
        """Test empty input followed by valid username."""
        mock_find.return_value = []
        with patch("builtins.input", side_effect=["", "", "Bob"]):
            result = prompt_username()
            assert result == "Bob"

    @patch("mentis.cli.find_existing_usernames")
    def test_prompt_username_with_existing(self, mock_find):
        """Test selecting from existing users."""
        mock_find.return_value = ["Alice", "Bob", "Charlie"]
        with patch("builtins.input", side_effect=["2"]):
            result = prompt_username()
            assert result == "Bob"

    @patch("mentis.cli.find_existing_usernames")
    def test_prompt_username_new_user(self, mock_find):
        """Test entering new username when existing users exist."""
        mock_find.return_value = ["Alice", "Bob"]
        with patch("builtins.input", side_effect=["Dave"]):
            result = prompt_username()
            assert result == "Dave"


class TestMain:
    """Tests for main CLI entry point."""

    @patch("mentis.cli.prompt_model_choice")
    @patch("mentis.cli.get_kg")
    @patch("mentis.cli.add_known_username")
    @patch("mentis.cli.prompt_username")
    @patch("mentis.cli.TomChatbot")
    @patch("builtins.input", side_effect=["quit"])
    def test_main_basic_flow(
        self,
        mock_input,
        mock_chatbot,
        mock_prompt_username,
        mock_add_known,
        mock_get_kg,
        mock_model_choice,
    ):
        """Test basic CLI flow."""
        mock_model_choice.return_value = "llama3.2"
        mock_prompt_username.return_value = "Alice"
        mock_kg = MagicMock()
        mock_get_kg.return_value = mock_kg
        mock_chatbot_instance = MagicMock()
        mock_chatbot.return_value = mock_chatbot_instance
        mock_chatbot_instance.process_message.return_value = "Hello!"

        # NOTE: simulating no arguments behavior to not have pytest -v affect this test
        # NOTE: any filename could really be passed here, not necessarily "mentis", since we don't check that
        with patch("sys.argv", ["mentis"]):
            # Run main - it should exit on quit
            exit_code = main()
            assert exit_code is None

    @patch("argparse.ArgumentParser.parse_args")
    @patch("mentis.cli.prompt_model_choice")
    @patch("mentis.cli.get_kg")
    @patch("mentis.cli.TomChatbot")
    def test_main_with_args(
        self, mock_chatbot, mock_get_kg, mock_model_choice, mock_parse_args
    ):
        """Test main with command-line arguments."""
        mock_parse_args.return_value = type(
            "Args",
            (),
            {"debug": True, "name": "TestUser", "rdf": False, "sparql": False},
        )()
        mock_model_choice.return_value = "llama3.2"
        mock_kg = MagicMock()
        mock_get_kg.return_value = mock_kg
        mock_chatbot_instance = MagicMock()
        mock_chatbot.return_value = mock_chatbot_instance
        mock_chatbot_instance.process_message.return_value = "Hello!"

        with patch("builtins.input", side_effect=["quit"]):
            # Should not raise
            main()
