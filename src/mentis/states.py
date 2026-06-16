"""Theory of Mind state definitions for Mentis."""

from dataclasses import dataclass, field, fields
from enum import StrEnum
from typing import List


class TomStateActionType(StrEnum):
    """Type of action to apply to ToM state."""

    ADD = "add"
    REMOVE = "remove"


@dataclass
class TomStateAction:
    """A single action to apply to a ToM state.

    Represents an add or remove operation for a specific ToM attribute value.
    """

    tom_key: str
    action: TomStateActionType
    value: str


@dataclass
class TomState:
    """Represents Theory of Mind state for an entity.

    Contains the five core mental state categories used in Theory of Mind modeling.
    Use dataclasses.asdict() to convert to dict, and TomState(**dict) to create from dict.
    Access attributes directly: state.beliefs, state.desires, etc.

    Get attribute names via: [f.name for f in fields(TomState)]
    """

    beliefs: List[str] = field(default_factory=list)
    desires: List[str] = field(default_factory=list)
    intentions: List[str] = field(default_factory=list)
    emotions: List[str] = field(default_factory=list)
    plans: List[str] = field(default_factory=list)

    def apply_action(self, action: TomStateAction) -> bool:
        """Apply a single action to this ToM state.

        Args:
            action: The action to apply

        Returns:
            True if action was applied and modified state, False if invalid or no change
        """
        if action.tom_key not in [f.name for f in fields(TomState)]:
            return False

        current_values = getattr(self, action.tom_key)

        if action.action == TomStateActionType.ADD:
            if action.value not in current_values:
                current_values.append(action.value)
                return True
            return False
        elif action.action == TomStateActionType.REMOVE:
            if action.value in current_values:
                current_values.remove(action.value)
                return True
            return False

        return False

    def apply_actions(self, actions: List[TomStateAction]) -> int:
        """Apply multiple actions to this ToM state.

        Args:
            actions: List of actions to apply

        Returns:
            Number of actions successfully applied
        """
        count = 0
        for action in actions:
            if self.apply_action(action):
                count += 1
        return count


def get_tom_attributes() -> List[str]:
    """Get list of ToM attribute names from TomState dataclass."""
    return [f.name for f in fields(TomState)]
