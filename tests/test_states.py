"""Tests for Theory of Mind state classes."""


from mentis.states import (
    TomState,
    TomStateAction,
    TomStateActionType,
    get_tom_attributes,
)


class TestTomStateActionType:
    """Tests for TomStateActionType StrEnum."""

    def test_add_value(self):
        """Test ADD action type value."""
        assert TomStateActionType.ADD == "add"
        assert str(TomStateActionType.ADD) == "add"

    def test_remove_value(self):
        """Test REMOVE action type value."""
        assert TomStateActionType.REMOVE == "remove"
        assert str(TomStateActionType.REMOVE) == "remove"

    def test_membership(self):
        """Test enum membership."""
        assert "add" in TomStateActionType
        assert "remove" in TomStateActionType
        assert "invalid" not in TomStateActionType

    def test_iteration(self):
        """Test iterating over enum values."""
        values = list(TomStateActionType)
        assert len(values) == 2
        assert TomStateActionType.ADD in values
        assert TomStateActionType.REMOVE in values


class TestTomStateAction:
    """Tests for TomStateAction dataclass."""

    def test_create_add_action(self):
        """Test creating an add action."""
        action = TomStateAction(
            tom_key="beliefs",
            action=TomStateActionType.ADD,
            value="the sky is blue"
        )
        assert action.tom_key == "beliefs"
        assert action.action == TomStateActionType.ADD
        assert action.value == "the sky is blue"

    def test_create_remove_action(self):
        """Test creating a remove action."""
        action = TomStateAction(
            tom_key="emotions",
            action=TomStateActionType.REMOVE,
            value="angry"
        )
        assert action.tom_key == "emotions"
        assert action.action == TomStateActionType.REMOVE
        assert action.value == "angry"

    def test_string_action_works(self):
        """Test that string action values work with StrEnum via conversion."""
        # When parsing from JSON, strings need to be converted to enum
        action_str = "add"
        assert action_str in TomStateActionType  # StrEnum supports 'in' with string
        
        # Convert string to enum
        action_enum = TomStateActionType(action_str)
        assert action_enum == TomStateActionType.ADD
        
        # Create action with enum
        action = TomStateAction(
            tom_key="desires",
            action=action_enum,
            value="to learn"
        )
        assert action.action == TomStateActionType.ADD
        assert isinstance(action.action, TomStateActionType)


class TestTomState:
    """Tests for TomState dataclass."""

    def test_default_empty_state(self):
        """Test default TomState has empty lists."""
        state = TomState()
        assert state.beliefs == []
        assert state.desires == []
        assert state.intentions == []
        assert state.emotions == []
        assert state.plans == []

    def test_create_with_values(self):
        """Test creating TomState with initial values."""
        state = TomState(
            beliefs=["the sky is blue"],
            emotions=["happy"]
        )
        assert state.beliefs == ["the sky is blue"]
        assert state.emotions == ["happy"]
        assert state.desires == []

    def test_apply_add_action(self):
        """Test applying an add action."""
        state = TomState()
        action = TomStateAction(
            tom_key="beliefs",
            action=TomStateActionType.ADD,
            value="new belief"
        )
        result = state.apply_action(action)
        assert result is True
        assert "new belief" in state.beliefs

    def test_apply_add_action_duplicate(self):
        """Test adding a duplicate value does nothing."""
        state = TomState(beliefs=["existing"])
        action = TomStateAction(
            tom_key="beliefs",
            action=TomStateActionType.ADD,
            value="existing"
        )
        state.apply_action(action)
        assert state.beliefs == ["existing"]  # No duplicate

    def test_apply_remove_action(self):
        """Test applying a remove action."""
        state = TomState(beliefs=["old belief", "new belief"])
        action = TomStateAction(
            tom_key="beliefs",
            action=TomStateActionType.REMOVE,
            value="old belief"
        )
        result = state.apply_action(action)
        assert result is True
        assert "old belief" not in state.beliefs
        assert "new belief" in state.beliefs

    def test_apply_remove_action_not_found(self):
        """Test removing a non-existent value does nothing."""
        state = TomState(beliefs=["existing"])
        action = TomStateAction(
            tom_key="beliefs",
            action=TomStateActionType.REMOVE,
            value="not there"
        )
        result = state.apply_action(action)
        assert result is False
        assert state.beliefs == ["existing"]

    def test_apply_invalid_key(self):
        """Test applying action with invalid tom_key fails gracefully."""
        state = TomState()
        action = TomStateAction(
            tom_key="invalid_key",
            action=TomStateActionType.ADD,
            value="value"
        )
        result = state.apply_action(action)
        assert result is False

    def test_apply_actions_multiple(self):
        """Test applying multiple actions."""
        state = TomState()
        actions = [
            TomStateAction("beliefs", "add", "belief1"),
            TomStateAction("beliefs", "add", "belief2"),
            TomStateAction("emotions", "add", "happy"),
        ]
        count = state.apply_actions(actions)
        assert count == 3
        assert state.beliefs == ["belief1", "belief2"]
        assert state.emotions == ["happy"]

    def test_apply_actions_with_invalid(self):
        """Test applying actions with some invalid ones."""
        state = TomState()
        actions = [
            TomStateAction("beliefs", "add", "valid"),
            TomStateAction("invalid", "add", "invalid"),  # Invalid key
        ]
        count = state.apply_actions(actions)
        assert count == 1  # Only 1 valid action applied
        assert state.beliefs == ["valid"]

    def test_apply_invalid_action_type(self):
        """Test applying action with invalid action type string."""
        state = TomState(beliefs=["existing"])
        # Manually create an action with invalid action (bypassing type hints)
        action = TomStateAction(tom_key="beliefs", action="invalid_action", value="test")
        result = state.apply_action(action)
        assert result is False
        # State should be unchanged
        assert state.beliefs == ["existing"]

    def test_asdict(self):
        """Test converting TomState to dict using dataclasses.asdict."""
        from dataclasses import asdict
        
        state = TomState(
            beliefs=["a", "b"],
            desires=["c"]
        )
        d = asdict(state)
        assert d == {
            "beliefs": ["a", "b"],
            "desires": ["c"],
            "intentions": [],
            "emotions": [],
            "plans": [],
        }

    def test_from_dict(self):
        """Test creating TomState from dict."""
        data = {
            "beliefs": ["a"],
            "desires": [],
            "intentions": [],
            "emotions": [],
            "plans": [],
        }
        state = TomState(**data)
        assert state.beliefs == ["a"]


class TestGetTomAttributes:
    """Tests for get_tom_attributes function."""

    def test_returns_all_attributes(self):
        """Test that all ToM attributes are returned."""
        attrs = get_tom_attributes()
        assert isinstance(attrs, list)
        assert len(attrs) == 5
        assert "beliefs" in attrs
        assert "desires" in attrs
        assert "intentions" in attrs
        assert "emotions" in attrs
        assert "plans" in attrs

    def test_returns_unique_values(self):
        """Test that all returned attributes are unique."""
        attrs = get_tom_attributes()
        assert len(attrs) == len(set(attrs))

    def test_matches_tomstate_fields(self):
        """Test that returned attributes match TomState field names."""
        attrs = get_tom_attributes()
        state_fields = [f.name for f in TomState.__dataclass_fields__.values()]
        assert set(attrs) == set(state_fields)
