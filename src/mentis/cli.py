"""CLI entry point for Mentis."""

import argparse
import ollama

from mentis.kg import get_kg
from mentis.chatbot import TomChatbot
from mentis.config import (
    get_model,
    set_model,
    find_existing_usernames,
    add_known_username,
)
from mentis.colors import (
    Colors,
    colorize,
    print_header,
    print_internal,
    print_bot,
    print_error,
)


def prompt_model_choice() -> str | None:
    """List available Ollama models and return user's choice."""
    print_header(" Available Ollama Models ")

    try:
        response = ollama.list()
        models = (
            response.models
            if hasattr(response, "models")
            else response.get("models", [])
        )

        if not models:
            print_internal("No models found. Using default: llama3.2")
            return "llama3.2"

        # Display models with numbers
        for i, model in enumerate(models, 1):
            # Use the Model class's .model attribute
            model_name = model.model
            size = (
                model.size
                if hasattr(model, "size")
                else getattr(model, "size", "Unknown")
            )

            # Format size in a readable way
            if isinstance(size, int):
                if size < 1024 * 1024 * 1024:  # < 1GB
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                else:
                    size_str = f"{size / (1024 * 1024 * 1024):.1f} GB"
            else:
                size_str = str(size)

            print(
                f"  {colorize(f'{i}.', Colors.BRIGHT_YELLOW)} {model_name:30s} {Colors.GRAY}{size_str}{Colors.RESET}"
            )

        # Prompt for selection
        while True:
            try:
                choice = input(
                    colorize(
                        "\nSelect model (number or name, default=1): ",
                        Colors.BRIGHT_GREEN,
                        Colors.BOLD,
                    )
                )
                if not choice:
                    return models[0].model

                # Try as number first
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(models):
                        return models[idx].model
                except ValueError:
                    pass

                # Try as model name
                for model in models:
                    if model.model == choice:
                        return choice

                print_error(
                    f"Invalid selection. Please enter a number 1-{len(models)} or a valid model name."
                )
            except KeyboardInterrupt:
                print("\n")
                return models[0].model

    except Exception as e:
        print_error(f"Could not list models: {e}")
        return "llama3.2"


def prompt_username():
    """Prompt user for their name, showing existing users."""
    existing_users = find_existing_usernames()

    if existing_users:
        print()
        for i, user in enumerate(existing_users, 1):
            print(f"  {colorize(f'{i}.', Colors.BRIGHT_YELLOW)} {user}")
        prompt_text = "\nEnter your name or number to pick from above: "
    else:
        prompt_text = "\nEnter your name: "

    while True:
        name = input(colorize(prompt_text, Colors.BRIGHT_GREEN, Colors.BOLD)).strip()
        if name:
            # Check if user entered a number to pick from existing
            if existing_users and name.isdigit():
                idx = int(name) - 1
                if 0 <= idx < len(existing_users):
                    return existing_users[idx]
            return name
        print_error("Please enter a valid name.")


def main():
    """Run the Mentis CLI."""
    parser = argparse.ArgumentParser(
        description="Mentis - Chatbot powered by Theory of Mind and Knowledge Graphs"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Log all prompts sent to Ollama"
    )
    parser.add_argument("--name", "-n", help="Your name (overrides prompt)")
    parser.add_argument(
        "--rdf",
        action="store_true",
        help="Use RDF/Turtle format for knowledge graph storage",
    )
    args = parser.parse_args()

    # Get username from CLI arg or prompt (always prompt if not via CLI)
    if args.name:
        username = args.name
    else:
        username = prompt_username()
        add_known_username(username)

    # Get KG implementation
    kg = get_kg(kg_type="rdf" if args.rdf else "graphml", username=username)

    kg_type_name = "RDF" if args.rdf else "GraphML"
    print_internal(f"Using {kg_type_name} knowledge graph for: {username}")

    # List and select model
    stored_model = get_model()
    if stored_model:
        model_name = stored_model
        print_internal(f"Using stored model: {model_name}")
    else:
        model_name = prompt_model_choice()
        set_model(model_name)
        print_internal(f"Using model: {model_name}")

    chatbot = TomChatbot(kg, model=model_name, debug=args.debug)

    print_header("Welcome to Mentis!")
    print_internal(
        f"Commands: 'quit' to exit, 'graph' to view knowledge graph. Talking to: {username}"
    )
    if args.debug:
        print_internal("Debug mode enabled - prompts will be logged")

    while True:
        try:
            # Use colored prompt with username
            prompt = colorize(f"\n{username}: ", Colors.BRIGHT_GREEN, Colors.BOLD)
            user_input = input(prompt)
            if user_input.lower() == "quit":
                print_internal("Goodbye!")
                break
            if user_input.lower() == "graph":
                kg.print_graph()
                continue

            response = chatbot.process_message(user_input, username)
            print_bot(response)
        except KeyboardInterrupt:
            print("\n")
            print_internal("Goodbye!")
            break
        except Exception as e:
            print_error(f"Error: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    main()
