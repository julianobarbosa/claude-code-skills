#!/bin/zsh

# Create ~/.claude/skills directory if it doesn't exist
mkdir -p ~/.claude/skills

# Get the directory where this script is located
SCRIPT_DIR="$(dirname "$0")"
SKILLS_DIR="$SCRIPT_DIR/../skills"

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
        
        # Remove existing link/file if it exists
        [[ -e "$target" || -L "$target" ]] && rm -rf "$target"
        
        # Create symbolic link
        ln -s "$item" "$target"
        echo "Linked: $item_name"
    fi
done

echo "Skills installation complete!"
