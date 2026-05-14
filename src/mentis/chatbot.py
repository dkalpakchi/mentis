"""Chatbot that builds Theory of Mind knowledge graph from conversation."""

import json
import uuid
from typing import Dict, List

import ollama

from mentis.states import (
    TomState,
    TomStateAction,
    TomStateActionType,
    get_tom_attributes,
)
from mentis.kg.base import TomGraph
from mentis.prompts import (
    TOM_EXTRACTOR_PROMPT,
    ENTITY_EXTRACTOR_PROMPT,
    RELATIONSHIP_EXTRACTOR_PROMPT,
    CHAT_RESPONSE_PROMPT,
)
from mentis.colors import print_internal, print_debug_prompt, print_debug_output


class TomChatbot:
    """Chatbot that builds Theory of Mind knowledge graph from conversation with inline prompts."""

    def __init__(self, kg: TomGraph, model: str | None, debug: bool = False):
        self.kg = kg
        self.model = model
        self.debug = debug
        self.conversation_history = []
        self.session_id = str(uuid.uuid4())[:8]

    def _log_prompt(self, prompt: str, method: str = "GENERATE"):
        """Log prompt when in debug mode."""
        if self.debug:
            print_debug_prompt(prompt, method)

    def _log_output(self, text: str, method: str = "GENERATE"):
        """Log model output when in debug mode."""
        if self.debug:
            print_debug_output(text, method)

    def _parse_json(self, text: str) -> dict:
        """Safely parse JSON from text, handling edge cases."""
        # Fixing common problems with JSON
        text = text.replace("```json", "")
        text = text.replace("```", "")

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Fallback to just empty dict
            return {}

    def _llm_invoke(
        self,
        prompt_template: str,
        temperature: float = 0,
        **kwargs,
    ) -> dict:
        """Generic LLM invocation for extraction tasks.

        Args:
            prompt_template: The prompt template string with format placeholders
            temperature: Temperature for generation (default 0.2)
            **kwargs: Arguments to format into the prompt template

        Returns:
            Parsed JSON result from LLM response
        """
        if self.model is None:
            return {}

        rendered = prompt_template.format(**kwargs)
        self._log_prompt(rendered, "generate")
        response = ollama.generate(
            model=self.model, prompt=rendered, options={"temperature": temperature}
        )
        raw_output = response["response"]
        self._log_output(raw_output, "generate")
        return self._parse_json(raw_output)

    def _extract_tom_from_text(
        self,
        text: str,
        entities: List[str] | None = None,
        relationships: List[Dict] | None = None,
        existing_tom: Dict | None = None,
        speaker: str = "user",
    ) -> List[TomStateAction]:
        """Use LLM to extract ToM state changes from text with entity/relationship context.

        Returns a list of TomStateAction objects representing add/remove operations.
        Invalid actions are filtered out.
        """
        result = self._llm_invoke(
            TOM_EXTRACTOR_PROMPT,
            text=text,
            speaker=speaker,
            entities=json.dumps(entities or []),
            relationships=json.dumps(relationships or []),
            existing_tom=json.dumps(existing_tom or {}),
        )

        # Parse actions, filtering out invalid ones
        actions = []
        if isinstance(result, list):
            for item in result:
                try:
                    action_str = item.get("action", "")
                    if action_str not in TomStateActionType:
                        continue
                    action = TomStateAction(
                        tom_key=item["tom_key"],
                        action=TomStateActionType(action_str),  # Convert string to enum
                        value=item["value"],
                    )
                    actions.append(action)
                except KeyError, TypeError, ValueError:
                    continue
        return actions

    def _extract_entities(self, text: str) -> List[str]:
        """Extract entity names from text."""
        result = self._llm_invoke(ENTITY_EXTRACTOR_PROMPT, text=text)
        return result if isinstance(result, list) else []

    def _extract_relationships(
        self, text: str, entities: List[str], speaker: str = "user"
    ) -> List[Dict]:
        """Extract relationships between entities."""
        result = self._llm_invoke(
            RELATIONSHIP_EXTRACTOR_PROMPT,
            text=text,
            entities=json.dumps(entities),
            speaker=speaker,
        )
        return result if isinstance(result, list) else []

    def _generate_response(self, text: str, speaker: str) -> str:
        """Generate chatbot response using context from knowledge graph.

        For RDF-based KGs, uses SPARQL queries to fetch only relevant ToM data.
        For GraphML-based KGs, uses the stored JSON-encoded attributes.
        """
        if self.model is None:
            return "The model is needed"

        history_text = "\n".join(self.conversation_history[-5:])

        # Use query methods - RDF uses SPARQL, GraphML uses defaults via get_entity_info
        tom_data = {
            attr: self.kg.query_tom(speaker, attr) for attr in get_tom_attributes()
        }

        # Query for relevant relationships involving this speaker
        relationships = self.kg.query_relationships(speaker)

        # Build ToM context - only include non-empty sections
        tom_sections = []
        for attr, values in tom_data.items():
            if values:
                # Capitalize first letter for display
                label = attr[0].upper() + attr[1:]
                tom_sections.append(f"{label}: {', '.join(values)}")

        # Add relationship context if available (from RDF queries)
        if relationships:
            rel_descriptions = []
            for rel in relationships:
                rel_type = rel.get("type", "related_to")
                target = rel.get("target", "someone")
                rel_descriptions.append(f"{rel_type} {target}")
            if rel_descriptions:
                tom_sections.append(f"Relationships: {', '.join(rel_descriptions)}")

        tom_context = (
            "\n".join(tom_sections)
            if tom_sections
            else "No Theory of Mind information available yet."
        )

        rendered = CHAT_RESPONSE_PROMPT.format(
            speaker=speaker,
            history=history_text,
            tom_context=tom_context,
        )

        # Log system and user messages in debug mode
        if self.debug:
            self._log_prompt(rendered, "CHAT[SYSTEM]")
            self._log_prompt(text, "CHAT[USER]")

        response = ollama.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": rendered},
                {"role": "user", "content": text},
            ],
            options={"temperature": 0},
        )
        raw_output = response["message"]["content"]
        self._log_output(raw_output, "CHAT")
        return raw_output

    def process_message(self, text: str, speaker: str = "user", verbose: bool = True):
        """Process user message and update knowledge graph.

        Uses sequential extraction with KG memory:
        1. Get existing entities and ToM state from KG
        2. Extract new entities
        3. Extract new relationships using all entities (existing + new)
        4. Extract ToM with full context (existing ToM, all entities, all relationships)
        5. Update KG: add entities, relationships, and set complete ToM state
        """
        if verbose:
            print_internal(f"Processing: '{text[:50]}...'")

        # Get existing context from KG
        existing_entities = self.kg.get_all_entities()
        existing_tom = self.kg.get_entity_info(speaker)

        if verbose:
            print_internal(f"Existing entities: {existing_entities}")
            print_internal(f"Existing ToM: {existing_tom}")

        # Extract new entities from text
        new_entities = self._extract_entities(text)
        if verbose:
            print_internal(f"New entities: {new_entities}")

        # Combine existing and new entities
        all_entities = list(set(existing_entities + new_entities))

        # Extract relationships using all entities
        relationships = self._extract_relationships(text, all_entities, speaker)
        if verbose:
            print_internal(f"Relationships: {relationships}")

        # Extract ToM state changes with full context
        tom_actions = self._extract_tom_from_text(
            text,
            entities=all_entities,
            relationships=relationships,
            existing_tom=existing_tom,
            speaker=speaker,
        )
        if verbose:
            print_internal(f"ToM actions: {tom_actions}")

        # Update KG: add entities first
        self.kg.add_entity(speaker)
        for entity in new_entities:
            if entity != speaker:
                self.kg.add_entity(entity)

        # Add relationships
        for rel in relationships:
            if rel.get("target"):
                self.kg.add_relationship(
                    rel.get("source", speaker),
                    rel["target"],
                    rel.get("type", "MENTIONS"),
                    rel.get("context", ""),
                )

        # Apply ToM actions: convert existing_tom to TomState, apply actions, save back
        if tom_actions:
            # Build TomState from existing ToM data
            tom_state = TomState(
                **{attr: existing_tom.get(attr, []) for attr in get_tom_attributes()}
            )
            tom_state.apply_actions(tom_actions)

            # Save updated state back to KG
            for attr in get_tom_attributes():
                values = getattr(tom_state, attr)
                self.kg.set_tom(speaker, attr, values)

        # Save graph
        self.kg.save()

        # Generate response
        response = self._generate_response(text, speaker)

        # Update conversation history
        self.conversation_history.append(f"User: {text}")
        self.conversation_history.append(f"Assistant: {response}")

        return response
