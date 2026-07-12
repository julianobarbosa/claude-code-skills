#!/bin/zsh

# Create ~/.claude/skills directory if it doesn't exist
mkdir -p ~/.claude/skills

# Get the directory where this script is located
SCRIPT_DIR="$(dirname "$0")"
SKILLS_DIR="$(cd "$SCRIPT_DIR/../skills" && pwd)" || {
    echo "Error: Cannot resolve skills directory"
    exit 1
}

# Check if skills directory exists
if [[ ! -d "$SKILLS_DIR" ]]; then
    echo "Error: skills directory not found at $SKILLS_DIR"
    exit 1
fi

# Create symbolic links for each item in skills directory
for item in "$SKILLS_DIR"/*; do
    if [[ -e "$item" ]]; then
        item_name="$(basename "$item")"
        target="$HOME/.claude/skills/$item_name"

        # Validate target path for safety
        if [[ "$target" != "$HOME/.claude/skills/"* ]]; then
            echo "Error: Invalid target path $target"
            exit 1
        fi

        # Remove existing link/file if it exists
        if [[ -L "$target" ]]; then
            # Remove existing symlink
            rm "$target"
        elif [[ -e "$target" ]]; then
            # Target exists but is not a symlink - warn and skip
            echo "Warning: $target exists and is not a symlink. Skipping $item_name."
            continue
        fi

        # Create symbolic link
        ln -s "$item" "$target"
        echo "Linked: $item_name"
    fi
done

echo "Skills installation complete!"
