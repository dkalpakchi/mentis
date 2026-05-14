"""Tests for TomChatbot."""

import tempfile
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from mentis.kg.graphml import TomGraphGraphML as TomGraph
from mentis.chatbot import TomChatbot


@pytest.fixture
def temp_kg():
    """Create a temporary TomGraph for testing."""
    with tempfile.NamedTemporaryFile(suffix=".graphml", delete=False) as f:
        temp_path = f.name

    kg = TomGraph(temp_path)
    yield kg

    # Cleanup
    if Path(temp_path).exists():
        os.unlink(temp_path)


@pytest.fixture
def mock_ollama():
    """Mock ollama.generate and ollama.chat to return predictable responses."""
    with patch("ollama.generate") as mock_generate, patch("ollama.chat") as mock_chat:
        # Create a combined mock that handles both
        class CombinedMock:
            def __call__(self, *args, **kwargs):
                # Check which function was called by looking at args
                if "messages" in kwargs or (
                    len(args) > 0 and "messages" in args[0]
                    if isinstance(args[0], dict)
                    else False
                ):
                    return mock_chat(*args, **kwargs)
                return mock_generate(*args, **kwargs)

        # Actually, simpler: just patch both separately and let the test set side_effect on each
        yield mock_generate, mock_chat


def test_chatbot_init(temp_kg):
    """Test TomChatbot initialization."""
    chatbot = TomChatbot(temp_kg, model="test-model")

    assert chatbot.kg == temp_kg
    assert chatbot.model == "test-model"
    assert chatbot.conversation_history == []
    assert len(chatbot.session_id) == 8


def test_parse_json_valid(temp_kg):
    """Test JSON parsing with valid JSON."""
    chatbot = TomChatbot(temp_kg, model="test-model")

    result = chatbot._parse_json('{"key": "value"}')
    assert result == {"key": "value"}


def test_parse_json_with_markdown(temp_kg):
    """Test JSON parsing with markdown code blocks."""
    chatbot = TomChatbot(temp_kg, model="test-model")

    result = chatbot._parse_json('```json\n{"key": "value"}\n```')
    assert result == {"key": "value"}


def test_parse_json_invalid(temp_kg):
    """Test JSON parsing with invalid JSON."""
    chatbot = TomChatbot(temp_kg, model="test-model")

    result = chatbot._parse_json("not valid json")
    assert result == {}


def test_extract_entities(mock_ollama, temp_kg):
    """Test entity extraction."""
    mock_generate, mock_chat = mock_ollama
    mock_generate.return_value = {"response": '["Alice", "Bob"]'}

    chatbot = TomChatbot(temp_kg, model="test-model")
    entities = chatbot._extract_entities("Alice and Bob are friends")

    assert entities == ["Alice", "Bob"]
    mock_generate.assert_called_once()


def test_extract_entities_empty(mock_ollama, temp_kg):
    """Test entity extraction with empty result."""
    mock_generate, mock_chat = mock_ollama
    mock_generate.return_value = {"response": "[]"}

    chatbot = TomChatbot(temp_kg, model="test-model")
    entities = chatbot._extract_entities("No entities here")

    assert entities == []


def test_extract_tom_from_text(mock_ollama, temp_kg):
    """Test ToM extraction from text."""
    from mentis import TomStateAction, TomStateActionType

    mock_generate, mock_chat = mock_ollama
    # Mock returns actions now
    mock_generate.return_value = {
        "response": '[{"tom_key": "beliefs", "action": "add", "value": "test"}]'
    }

    chatbot = TomChatbot(temp_kg, model="test-model")
    actions = chatbot._extract_tom_from_text("I believe test", "user")

    assert len(actions) == 1
    assert isinstance(actions[0], TomStateAction)
    assert actions[0].tom_key == "beliefs"
    assert actions[0].action == TomStateActionType.ADD
    assert actions[0].value == "test"


def test_generate_response(mock_ollama, temp_kg):
    """Test response generation."""
    mock_generate, mock_chat = mock_ollama
    mock_chat.return_value = {"message": {"content": "Hello there!"}}

    chatbot = TomChatbot(temp_kg, model="test-model")
    chatbot.conversation_history = ["User: Hi", "Assistant: Hey"]

    response = chatbot._generate_response("How are you?", "user")

    assert response == "Hello there!"


def test_tom_context_in_prompt(mock_ollama, temp_kg):
    """Test that ToM context is correctly formatted in the chat prompt."""

    mock_generate, mock_chat = mock_ollama

    # Set up ToM data in the graph
    kg = temp_kg
    kg.add_entity("user")
    kg.update_tom("user", "beliefs", ["the sky is blue", "people are kind"])
    kg.update_tom("user", "emotions", ["happy", "excited"])
    kg.update_tom("user", "desires", ["to learn"])

    # Create chatbot and mock the chat call
    chatbot = TomChatbot(kg, model="test-model")
    chatbot.conversation_history = []

    # Capture what was passed to ollama.chat
    captured_messages = []

    def capture_chat(*args, **kwargs):
        captured_messages.append(kwargs.get("messages", []))
        return {"message": {"content": "Test response"}}

    mock_chat.side_effect = capture_chat

    # Call _generate_response
    chatbot._generate_response("What do you know about me?", "user")

    # Verify the chat was called
    assert len(captured_messages) == 1
    messages = captured_messages[0]

    # Find the system message
    system_msg = next((m for m in messages if m["role"] == "system"), None)
    assert system_msg is not None

    system_content = system_msg["content"]

    # Verify ToM context is in the prompt
    assert "Theory of Mind context for user:" in system_content

    # Verify the ToM attributes are properly formatted (not JSON strings)
    # Note: order may vary due to set operations, so check for substrings
    assert (
        "Beliefs:" in system_content
        and "the sky is blue" in system_content
        and "people are kind" in system_content
    )
    assert (
        "Emotions:" in system_content
        and "happy" in system_content
        and "excited" in system_content
    )
    assert "Desires:" in system_content and "to learn" in system_content

    # Make sure there are no JSON-encoded lists in the output
    assert '["' not in system_content


def test_tom_context_empty(mock_ollama, temp_kg):
    """Test that empty ToM context shows 'No Theory of Mind information available yet.'"""
    mock_generate, mock_chat = mock_ollama

    kg = temp_kg
    kg.add_entity("user")
    # Don't add any ToM data - leave it empty

    chatbot = TomChatbot(kg, model="test-model")
    chatbot.conversation_history = []

    captured_messages = []

    def capture_chat(*args, **kwargs):
        captured_messages.append(kwargs.get("messages", []))
        return {"message": {"content": "Test response"}}

    mock_chat.side_effect = capture_chat

    chatbot._generate_response("Hello", "user")

    system_msg = next((m for m in captured_messages[0] if m["role"] == "system"), None)
    assert system_msg is not None
    assert "No Theory of Mind information available yet." in system_msg["content"]


def test_process_message(mock_ollama, temp_kg):
    """Test full message processing."""
    mock_generate, mock_chat = mock_ollama
    # Mock responses for each extraction step
    # Order: entities, relationships, tom_actions (sequential extraction)
    # Last one is for chat() call (response)
    mock_generate.side_effect = [
        {"response": '["Alice"]'},  # entities
        {"response": "[]"},  # relationships
        {
            "response": '[{"tom_key": "emotions", "action": "add", "value": "happy"}]'
        },  # tom actions
    ]
    mock_chat.return_value = {"message": {"content": "Hello!"}}

    chatbot = TomChatbot(temp_kg, model="test-model")
    response = chatbot.process_message("I am happy", "user")

    assert response == "Hello!"
    assert len(chatbot.conversation_history) == 2


def test_parse_json_with_code_block_markers(temp_kg):
    """Test JSON parsing with various code block markers."""
    chatbot = TomChatbot(temp_kg, model="test-model")

    # Test with ```json
    result = chatbot._parse_json('```json\n{"key": "value"}\n```')
    assert result == {"key": "value"}

    # Test with just ```
    result = chatbot._parse_json('```{"key": "value"}```')
    assert result == {"key": "value"}


def test_parse_json_empty_string(temp_kg):
    """Test JSON parsing with empty string."""
    chatbot = TomChatbot(temp_kg, model="test-model")
    result = chatbot._parse_json("")
    assert result == {}


def test_llm_invoke_with_temperature(mock_ollama, temp_kg):
    """Test _llm_invoke with custom temperature."""
    from mentis.prompts import ENTITY_EXTRACTOR_PROMPT

    mock_generate, mock_chat = mock_ollama
    mock_generate.return_value = {"response": "[]"}

    chatbot = TomChatbot(temp_kg, model="test-model")
    result = chatbot._llm_invoke(
        ENTITY_EXTRACTOR_PROMPT, temperature=0.5, text="test text"
    )

    assert result == []
    # Verify temperature was passed
    call_kwargs = mock_generate.call_args[1]
    assert call_kwargs["options"]["temperature"] == 0.5


def test_log_prompt_debug_mode(capsys, temp_kg):
    """Test that _log_prompt outputs when debug=True."""
    chatbot = TomChatbot(temp_kg, model="test-model", debug=True)
    chatbot._log_prompt("test prompt", "TEST")
    captured = capsys.readouterr()
    assert "test prompt" in captured.out


def test_log_prompt_no_debug(capsys, temp_kg):
    """Test that _log_prompt does not output when debug=False."""
    chatbot = TomChatbot(temp_kg, model="test-model", debug=False)
    chatbot._log_prompt("test prompt", "TEST")
    captured = capsys.readouterr()
    assert captured.out == ""


def test_extract_tom_with_malformed_action(mock_ollama, temp_kg):
    """Test ToM extraction with malformed action data."""
    mock_generate, mock_chat = mock_ollama
    # Return malformed action (missing tom_key)
    mock_generate.return_value = {
        "response": '[{"action": "add", "value": "test"}]'  # Missing tom_key
    }

    chatbot = TomChatbot(temp_kg, model="test-model")
    actions = chatbot._extract_tom_from_text("test", "user")

    # Should return empty list since action is invalid
    assert actions == []


def test_extract_tom_with_invalid_action_type(mock_ollama, temp_kg):
    """Test ToM extraction with invalid action type."""
    mock_generate, mock_chat = mock_ollama
    mock_generate.return_value = {
        "response": '[{"tom_key": "beliefs", "action": "invalid", "value": "test"}]'
    }

    chatbot = TomChatbot(temp_kg, model="test-model")
    actions = chatbot._extract_tom_from_text("test", "user")

    # Invalid action type should be filtered out
    assert actions == []


def test_process_message_with_existing_tom_string_values(temp_kg):
    """
    Test that process_message handles existing ToM correctly.
    get_entity_info now returns parsed lists, not JSON strings.
    """
    from unittest.mock import patch

    # First, add an entity and set ToM via update_tom
    temp_kg.add_entity("user")
    temp_kg.update_tom("user", "plans", ["initial plan"])

    # Verify that get_entity_info returns parsed lists
    existing_tom = temp_kg.get_entity_info("user")
    assert existing_tom["plans"] == ["initial plan"]  # Now returns list

    # Now process a second message - should work correctly
    chatbot = TomChatbot(temp_kg, model="test-model")

    with patch("ollama.generate") as mock_gen, patch("ollama.chat") as mock_chat:
        mock_gen.side_effect = [
            {"response": "[]"},  # entities (no new entities)
            {"response": "[]"},  # relationships
            {
                "response": '[{"tom_key": "plans", "action": "add", "value": "meet Bob"}]'
            },  # tom actions
        ]
        mock_chat.return_value = {"message": {"content": "ok"}}

        response = chatbot.process_message("Gonna meet with my mate Bob", "user", verbose=False)
        assert response == "ok"
        
        # Verify ToM was updated with both values
        updated_tom = temp_kg.get_entity_info("user")
        assert "initial plan" in updated_tom["plans"]
        assert "meet Bob" in updated_tom["plans"]
