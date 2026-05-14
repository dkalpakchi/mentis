"""ANSI color utilities for CLI output."""


# ANSI color codes
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    GRAY = "\033[38;2;128;128;128m"
    DIM_WHITE = "\033[38;2;200;200;200m"

    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright foreground colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


def colorize(text: str, *colors: str) -> str:
    """Wrap text with ANSI color codes."""
    if not text:
        return text
    color_code = "".join(colors)
    return f"{color_code}{text}{Colors.RESET}"


def print_header(text: str):
    """Print a header with bright cyan and box drawing characters."""
    box = colorize("╔" + "═" * (len(text) + 2) + "╗", Colors.BRIGHT_CYAN)
    line = colorize(f"║ {text} ║", Colors.BRIGHT_CYAN)
    box_end = colorize("╚" + "═" * (len(text) + 2) + "╝", Colors.BRIGHT_CYAN)
    print(f"\n{box}\n{line}\n{box_end}\n")


def print_user(text: str):
    """Print user message in bright green."""
    prefix = colorize("You: ", Colors.BRIGHT_GREEN, Colors.BOLD)
    print(f"{prefix}{text}")


def print_bot(text: str):
    """Print bot message in bright blue with a robot indicator."""
    prefix = colorize("Bot: ", Colors.BRIGHT_BLUE, Colors.BOLD)
    print(f"{prefix}{text}")


def print_internal(text: str):
    """Print internal system messages in gray."""
    # Use a medium gray color (RGB 128,128,128) via 24-bit color escape
    print(f"{Colors.GRAY}  [{text}]{Colors.RESET}")


def print_debug_prompt(prompt: str, method: str = "GENERATE"):
    """Print debug prompt in full with distinct formatting."""
    # Use a box drawing format with bright magenta for DEBUG label
    # and dim white for the actual prompt content
    DEBUG_LABEL = colorize(f"[DEBUG {method}]", Colors.BRIGHT_MAGENTA, Colors.BOLD)

    # Print with a separator line above and below
    separator = colorize("-" * 60, Colors.DIM_WHITE)
    print(f"\n{DEBUG_LABEL}")
    print(f"{separator}")
    print(f"{Colors.DIM_WHITE}{prompt}{Colors.RESET}")
    print(f"{separator}\n")


def print_debug_output(text: str, method: str = "GENERATE"):
    """Print debug output (model response) in distinct formatting."""
    OUTPUT_LABEL = colorize(f"[DEBUG {method} OUTPUT]", Colors.BRIGHT_CYAN, Colors.BOLD)

    # Print with a separator line above and below
    separator = colorize("-" * 60, Colors.DIM_WHITE)
    print(f"{OUTPUT_LABEL}")
    print(f"{separator}")
    print(f"{Colors.DIM_WHITE}{text}{Colors.RESET}")
    print(f"{separator}\n")


def print_separator(color: str = Colors.GRAY, length: int = 40):
    """Print a colored separator line."""
    print(f"{color}  {'-' * length}{Colors.RESET}")


def print_success(text: str):
    """Print success messages in bright green."""
    print(colorize(f"  ✓ {text}", Colors.BRIGHT_GREEN))


def print_error(text: str):
    """Print error messages in bright red."""
    print(colorize(f"  ✗ {text}", Colors.BRIGHT_RED))


def print_tom_label(attr: str, values: list):
    """Print a ToM attribute with colored label."""
    colors_map = {
        "beliefs": Colors.BRIGHT_BLUE,
        "desires": Colors.BRIGHT_MAGENTA,
        "intentions": Colors.BRIGHT_YELLOW,
        "emotions": Colors.BRIGHT_RED,
        "plans": Colors.BRIGHT_GREEN,
    }
    color = colors_map.get(attr, Colors.BRIGHT_WHITE)
    label = colorize(f"  {attr}:", color, Colors.BOLD)
    values_str = colorize(", ".join(values), Colors.WHITE)
    print(f"{label} {values_str}")


def print_entity(entity: str, entity_type: str = "person"):
    """Print an entity with type in color."""
    type_colors = {
        "person": Colors.BRIGHT_GREEN,
        "organization": Colors.BRIGHT_YELLOW,
        "location": Colors.BRIGHT_CYAN,
        "concept": Colors.BRIGHT_MAGENTA,
    }
    color = type_colors.get(entity_type, Colors.BRIGHT_WHITE)
    print(colorize(f"  • {entity} ({entity_type})", color))


def print_relationship(source: str, target: str, rel_type: str, context: str = ""):
    """Print a relationship with color."""
    arrow = colorize(" --> ", Colors.DIM)
    rel = colorize(f"[{rel_type}]", Colors.BRIGHT_CYAN)
    ctx = colorize(f" [{context}]", Colors.DIM) if context else ""
    print(f"  {source}{arrow}{rel}{ctx} {target}")
