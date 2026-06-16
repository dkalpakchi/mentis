from mentis.states import get_tom_attributes

# Build the keys list from TomState fields
TOM_KEYS = ", ".join(get_tom_attributes())

TOM_EXTRACTOR_PROMPT = f"""You are an expert Theory of Mind analyst. Extract mental state changes from text.

Analyze the text and identify ALL changes to the speaker's mental state, including IMPLICIT changes.
Return ONLY a JSON list of action objects.
Each action must have: tom_key (one of: {TOM_KEYS}), action ("add" or "remove"), value (string).
If no changes detected, return an empty list.
Do NOT add any other keys, text, explanations, or markdown formatting.

IMPORTANT RULES for implicit feedback detection:
- If the speaker's statement CONTRADICTS an existing belief/desire/intention/plan, REMOVE the old one and ADD the new one.
- If the speaker's emotional tone SHIFTS (e.g., from angry to happy), REMOVE the old emotion and ADD the new one.
- If the speaker ABANDONS a plan or changes direction, REMOVE the old plan and ADD the new one.
- If the speaker indicates a plan is COMPLETED/DONE/FINISHED (e.g., "I did it", "That's done", "Finished"), REMOVE that plan from the plans list.
- If existing ToM values are no longer relevant or contradicted, use "remove" action.
- Be PROACTIVE: infer removals from implicit feedback, not just explicit statements.

Example actions:
[{{{{"tom_key": "beliefs", "action": "add", "value": "the sky is blue"}}}},
 {{{{"tom_key": "emotions", "action": "remove", "value": "angry"}}}}]

Speaker: {{speaker}}

Existing mental state for {{speaker}}: {{existing_tom}}
Known entities in conversation: {{entities}}
Known relationships: {{relationships}}

New text to analyze: {{text}}"""

ENTITY_EXTRACTOR_PROMPT = """You are an expert Named Entity Recognition system.

Extract all named entities (persons, organizations, locations, concepts) from this text.
Do NOT extract pronouns (he, she, they, it, etc.) or generic terms.
Return ONLY a JSON list of strings with the entity names.
If no entities found, return an empty list.

Text: {text}"""

RELATIONSHIP_EXTRACTOR_PROMPT = """You are an expert relationship extraction system.

Identify all explicit and implicit relationships between entities in this text.
Return ONLY a JSON list of relationship objects.
Each object must have: source (string), target (string), type (string), context (optional string).
Make type `snake_case`.
If no relationships found, return an empty list.

Speaker: {speaker}
Assume the speaker ({speaker}) is the source unless another entity is clearly the actor.
Use PAST, PRESENT, or FUTURE tense in the type when appropriate.

Known entities: {entities}
Text: {text}"""

CHAT_RESPONSE_PROMPT = """You are a helpful, empathetic assistant with Theory of Mind awareness.
You have access to a knowledge graph containing Theory of Mind information about the user. Use this context to provide more personalized, understanding responses.

Conversation history:
{history}

Theory of Mind context for {speaker}:
{tom_context}

Respond naturally and empathetically based on this context."""
