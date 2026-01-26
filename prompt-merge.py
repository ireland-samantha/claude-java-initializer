#!/usr/bin/env python3
"""
Merge Claude Code prompt templates into a single CLAUDE.md file.

Usage:
    ./prompt-merge.py --list          List all available templates
    ./prompt-merge.py go              Interactive selection and merge
    ./prompt-merge.py go -o FILE      Output to specific file (default: CLAUDE.md)
"""

import argparse
import os
import sys
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "templates"


def get_all_templates() -> list[dict]:
    """Scan templates directory and return all .md files with metadata."""
    templates = []

    for md_file in sorted(TEMPLATES_DIR.rglob("*.md")):
        rel_path = md_file.relative_to(TEMPLATES_DIR)

        # Read first few lines to get title and description
        title = rel_path.stem
        description = ""
        extends = None

        with open(md_file, "r") as f:
            lines = f.readlines()
            for line in lines[:10]:
                line = line.strip()
                if line.startswith("# "):
                    title = line[2:].strip()
                elif line.startswith("> **Extends:**"):
                    extends = line
                elif line and not line.startswith("#") and not line.startswith(">"):
                    description = line[:80]
                    if len(line) > 80:
                        description += "..."
                    break

        templates.append({
            "path": md_file,
            "rel_path": str(rel_path),
            "title": title,
            "description": description,
            "extends": extends,
            "is_base": "base" in md_file.name.lower(),
        })

    return templates


def list_templates():
    """Print all available templates."""
    templates = get_all_templates()

    print("\nAvailable Templates:")
    print("=" * 60)

    for t in templates:
        base_marker = " [BASE]" if t["is_base"] else ""
        print(f"\n  {t['rel_path']}{base_marker}")
        print(f"    Title: {t['title']}")
        if t["description"]:
            print(f"    {t['description']}")
        if t["extends"]:
            print(f"    {t['extends']}")

    print("\n" + "=" * 60)
    print(f"Total: {len(templates)} template(s)\n")


def interactive_select(templates: list[dict]) -> list[dict]:
    """Interactive checkbox selection using terminal."""
    selected = [False] * len(templates)
    current = 0

    def write(text):
        """Write text with proper line endings for raw mode."""
        sys.stdout.write(text.replace("\n", "\r\n"))
        sys.stdout.flush()

    def render():
        # Clear screen and move cursor to top
        write("\033[2J\033[H")
        write("Select templates to merge (SPACE to toggle, ENTER to confirm, q to quit):\n\n")

        for i, t in enumerate(templates):
            cursor = ">" if i == current else " "
            check = "[x]" if selected[i] else "[ ]"
            base_marker = " [BASE]" if t["is_base"] else ""
            write(f" {cursor} {check} {t['rel_path']}{base_marker}\n")
            write(f"       {t['title']}\n")

        count = sum(selected)
        write(f"\n{count} template(s) selected")

    # Set terminal to raw mode for single keypress reading
    import tty
    import termios

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)

        while True:
            render()

            ch = sys.stdin.read(1)

            # Handle arrow keys (escape sequences)
            if ch == "\x1b":
                ch2 = sys.stdin.read(1)
                if ch2 == "[":
                    ch3 = sys.stdin.read(1)
                    if ch3 == "A":  # Up arrow
                        current = (current - 1) % len(templates)
                    elif ch3 == "B":  # Down arrow
                        current = (current + 1) % len(templates)
            elif ch == "k":  # vim up
                current = (current - 1) % len(templates)
            elif ch == "j":  # vim down
                current = (current + 1) % len(templates)
            elif ch == " ":  # Space to toggle
                selected[current] = not selected[current]
            elif ch == "\r" or ch == "\n":  # Enter to confirm
                break
            elif ch == "q" or ch == "\x03":  # q or Ctrl+C to quit
                write("\033[2J\033[H")  # Clear screen
                write("Cancelled.\n")
                return []
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    # Clear screen after selection
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()

    return [t for i, t in enumerate(templates) if selected[i]]


def merge_templates(templates: list[dict], output_path: str):
    """Merge selected templates into a single file."""
    if not templates:
        print("No templates selected.")
        return

    # Sort: base templates first, then extensions
    templates = sorted(templates, key=lambda t: (not t["is_base"], t["rel_path"]))

    merged_content = []
    merged_content.append("# CLAUDE.md")
    merged_content.append("")
    merged_content.append("<!-- Generated by prompt-merge.py -->")
    merged_content.append(f"<!-- Sources: {', '.join(t['rel_path'] for t in templates)} -->")
    merged_content.append("")

    for i, t in enumerate(templates):
        with open(t["path"], "r") as f:
            content = f.read()

        # Remove the "Extends" note from extensions since we're merging
        lines = content.split("\n")
        filtered_lines = []
        skip_next_empty = False

        for line in lines:
            if line.startswith("> **Extends:**") or line.startswith("> This extension"):
                skip_next_empty = True
                continue
            if skip_next_empty and line.strip() == "":
                skip_next_empty = False
                continue
            if skip_next_empty and line.startswith(">"):
                continue
            skip_next_empty = False
            filtered_lines.append(line)

        content = "\n".join(filtered_lines)

        # Add separator between templates (except first)
        if i > 0:
            merged_content.append("")
            merged_content.append("---")
            merged_content.append("")

        merged_content.append(content.strip())

    merged_content.append("")

    # Write output
    output = "\n".join(merged_content)

    with open(output_path, "w") as f:
        f.write(output)

    print(f"Merged {len(templates)} template(s) into {output_path}")
    print("\nIncluded templates:")
    for t in templates:
        print(f"  - {t['rel_path']}")


def main():
    parser = argparse.ArgumentParser(
        description="Merge Claude Code prompt templates into a single CLAUDE.md file."
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available templates"
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=["go"],
        help="Command to run (go: interactive selection)"
    )
    parser.add_argument(
        "-o", "--output",
        default="CLAUDE.md",
        help="Output file path (default: CLAUDE.md)"
    )

    args = parser.parse_args()

    if args.list:
        list_templates()
    elif args.command == "go":
        templates = get_all_templates()
        if not templates:
            print("No templates found in", TEMPLATES_DIR)
            sys.exit(1)

        selected = interactive_select(templates)
        if selected:
            merge_templates(selected, args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
