# softmoth/zsh-vim-mode Reference

Comprehensive guide for the zsh-vim-mode plugin by softmoth.

**Repository:** https://github.com/softmoth/zsh-vim-mode

## Requirements

- ZSH 5.3+ (full features)
- ZSH 5.0.8+ (text object support)

## Installation

### Manual

```bash
git clone https://github.com/softmoth/zsh-vim-mode.git ~/.zsh/zsh-vim-mode
```

Add to `~/.zshrc`:
```zsh
source ~/.zsh/zsh-vim-mode/zsh-vim-mode.plugin.zsh
```

### With Plugin Manager

**Zinit:**
```zsh
zinit light softmoth/zsh-vim-mode
```

**Antigen:**
```zsh
antigen bundle softmoth/zsh-vim-mode
```

**Zplug:**
```zsh
zplug "softmoth/zsh-vim-mode"
```

## Plugin Load Order

**Critical:** Load zsh-vim-mode LAST to avoid keybinding conflicts:

```zsh
# Correct order
source ~/.zsh/zsh-autosuggestions/zsh-autosuggestions.zsh
source ~/.zsh/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
source ~/.zsh/zsh-vim-mode/zsh-vim-mode.plugin.zsh  # LAST
```

## Configuration Variables

### Core Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `VIM_MODE_VICMD_KEY` | Key to enter NORMAL mode | `^[` (Escape) |
| `VIM_MODE_NO_DEFAULT_BINDINGS` | Disable built-in keybindings | unset |
| `VIM_MODE_TRACK_KEYMAP` | Toggle mode-sensitive feedback | `true` |
| `VIM_MODE_INITIAL_KEYMAP` | Starting mode | `viins` |

**Initial keymap options:**
- `viins` - Start in INSERT mode (default)
- `vicmd` - Start in NORMAL mode
- `last` - Remember last mode across prompts

### Cursor Styling

Define cursor appearance per mode:

```zsh
# Format: "color style"
# Colors: named (green, red) or hex (#RRGGBB)
# Styles: steady, blinking, block, underline, bar

MODE_CURSOR_VIINS="#00ff00 blinking bar"
MODE_CURSOR_VICMD="green block"
MODE_CURSOR_REPLACE="red block"
MODE_CURSOR_SEARCH="#ff00ff steady underline"
MODE_CURSOR_VISUAL="$MODE_CURSOR_VICMD steady bar"
MODE_CURSOR_VLINE="$MODE_CURSOR_VISUAL #00ffff"
```

**Style values:**
| Style | Description |
|-------|-------------|
| `block` | Full cursor block |
| `underline` | Underscore cursor |
| `bar` | Vertical line cursor |
| `steady` | No blinking |
| `blinking` | Blinking cursor |

### Mode Indicators

Customize prompt indicators per mode:

```zsh
# Uses zsh prompt expansion
MODE_INDICATOR_VIINS='%F{15}<%F{8}INSERT>%f'
MODE_INDICATOR_VICMD='%F{10}<%F{2}NORMAL>%f'
MODE_INDICATOR_REPLACE='%F{9}<%F{1}REPLACE>%f'
MODE_INDICATOR_SEARCH='%F{13}<%F{5}SEARCH>%f'
MODE_INDICATOR_VISUAL='%F{12}<%F{4}VISUAL>%f'
MODE_INDICATOR_VLINE='%F{12}<%F{4}V-LINE>%f'
```

**Auto-display:** If `RPS1`/`RPROMPT` is unset, indicators display automatically.

**Manual placement:** Use `${MODE_INDICATOR_PROMPT}` in your prompt when `prompt_subst` is enabled:
```zsh
setopt prompt_subst
RPROMPT='${MODE_INDICATOR_PROMPT}'
```

## Key Features

### Text Objects

Standard vim text objects work with operators (d, c, y, v):

| Text Object | Selects |
|-------------|---------|
| `iw` / `aw` | Inner/a word |
| `iW` / `aW` | Inner/a WORD |
| `i"` / `a"` | Inside/around double quotes |
| `i'` / `a'` | Inside/around single quotes |
| `` i` `` / `` a` `` | Inside/around backticks |
| `i(` / `a(` | Inside/around parentheses |
| `i[` / `a[` | Inside/around brackets |
| `i{` / `a{` | Inside/around braces |
| `i<` / `a<` | Inside/around angle brackets |

**Examples:**
- `ci"` - Change text inside double quotes
- `da(` - Delete text including parentheses
- `vi[` - Visual select inside brackets

### Surround Operations

Change, delete, or add surrounding characters:

| Command | Action |
|---------|--------|
| `cs"'` | Change surrounding `"` to `'` |
| `cs"(` | Change `"` to `(` |
| `ds(` | Delete surrounding parentheses |
| `ysaw"` | Surround a word with `"` |

### Visual Mode

| Key | Action |
|-----|--------|
| `v` | Character-wise visual |
| `V` | Line-wise visual |
| `a"` | Select around quotes |
| `i(` | Select inside parens |

### INSERT Mode Emacs Bindings

Emacs shortcuts available in INSERT mode:

| Key | Action |
|-----|--------|
| `Ctrl-A` | Beginning of line |
| `Ctrl-E` | End of line |
| `Ctrl-B` | Back one character |
| `Ctrl-F` | Forward one character |
| `Ctrl-K` | Kill to end of line |
| `Ctrl-U` | Kill to beginning of line |
| `Ctrl-W` | Kill word backward |
| `Ctrl-R` | Incremental history search |

## KEYTIMEOUT Configuration

The `KEYTIMEOUT` affects escape key behavior:

```zsh
# Default is 40 (400ms)
# Lower = faster mode switch, but may break multi-key sequences
export KEYTIMEOUT=20  # 200ms - reasonable compromise
```

**Issues with low KEYTIMEOUT:**
- Multi-key sequences (like `cs"'`) may not work
- Arrow keys might not function in some terminals

**Alternatives to reduce ESC delay:**

1. **Use Ctrl-[ instead of Escape** (sends ESC immediately)

2. **Remove double-ESC binding:**
```zsh
# In .zshrc before sourcing plugin
bindkey -M vicmd '\e' undefined-key
```

3. **Reassign NORMAL mode key:**
```zsh
VIM_MODE_VICMD_KEY='^X'  # Use Ctrl-X instead
```

4. **Bind jk/jj to escape:**
```zsh
bindkey -M viins 'jk' vi-cmd-mode
```

## Integration with Powerlevel10k

P10k has built-in vi mode support:

```zsh
# In ~/.p10k.zsh
typeset -g POWERLEVEL9K_RIGHT_PROMPT_ELEMENTS=(... vi_mode ...)

# Customize vi mode segment
typeset -g POWERLEVEL9K_VI_INSERT_MODE_STRING=''
typeset -g POWERLEVEL9K_VI_COMMAND_MODE_STRING='NORMAL'
typeset -g POWERLEVEL9K_VI_MODE_NORMAL_FOREGROUND=0
typeset -g POWERLEVEL9K_VI_MODE_NORMAL_BACKGROUND=2
```

When using P10k's vi_mode segment, you may want to disable zsh-vim-mode's indicator:
```zsh
MODE_INDICATOR_VIINS=''
MODE_INDICATOR_VICMD=''
# ... etc
```

## Troubleshooting

### Cursor Not Changing

1. **Check terminal support:** Not all terminals support cursor escape codes
   - Works: iTerm2, Alacritty, Kitty, GNOME Terminal
   - Limited: Apple Terminal, some SSH sessions

2. **Verify variable is set:**
```zsh
echo $MODE_CURSOR_VICMD
```

3. **Test manually:**
```zsh
echo -ne '\e[2 q'  # Should show block cursor
echo -ne '\e[6 q'  # Should show beam cursor
```

### Bindings Not Working

1. **Check load order:** Ensure zsh-vim-mode loads LAST

2. **Verify plugin loaded:**
```zsh
which -a zle-keymap-select
```

3. **Check for conflicts:**
```zsh
bindkey -M vicmd | grep -E "cs|ds|ys"
```

### Mode Indicator Not Showing

1. **Check RPROMPT:**
```zsh
echo $RPROMPT
```

2. **Force indicator:**
```zsh
setopt prompt_subst
RPROMPT='${MODE_INDICATOR_PROMPT}'
```

### Slow Mode Switching

1. Reduce `KEYTIMEOUT`:
```zsh
export KEYTIMEOUT=10
```

2. Use `Ctrl-[` instead of Escape

## Complete Configuration Example

```zsh
# ~/.zshrc

# Load plugin (after other plugins)
source ~/.zsh/zsh-vim-mode/zsh-vim-mode.plugin.zsh

# Key timeout
export KEYTIMEOUT=20

# Cursor styles
MODE_CURSOR_VIINS="green blinking bar"
MODE_CURSOR_VICMD="green block"
MODE_CURSOR_REPLACE="red blinking block"
MODE_CURSOR_SEARCH="yellow underline"
MODE_CURSOR_VISUAL="cyan block"
MODE_CURSOR_VLINE="magenta block"

# Mode indicators
MODE_INDICATOR_VIINS='%F{green}-- INSERT --%f'
MODE_INDICATOR_VICMD='%F{blue}-- NORMAL --%f'
MODE_INDICATOR_REPLACE='%F{red}-- REPLACE --%f'
MODE_INDICATOR_SEARCH='%F{yellow}-- SEARCH --%f'
MODE_INDICATOR_VISUAL='%F{cyan}-- VISUAL --%f'
MODE_INDICATOR_VLINE='%F{magenta}-- V-LINE --%f'

# Start in insert mode
VIM_MODE_INITIAL_KEYMAP=viins

# Alternative escape (optional)
bindkey -M viins 'jk' vi-cmd-mode
```

## External Resources

- GitHub: https://github.com/softmoth/zsh-vim-mode
- Oh My Zsh vi-mode: https://github.com/ohmyzsh/ohmyzsh/tree/master/plugins/vi-mode
- jeffreytse/zsh-vi-mode: https://github.com/jeffreytse/zsh-vi-mode
