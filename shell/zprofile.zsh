# Login shells: select native Homebrew, then make mise shims available to agents.
if [[ -x /opt/homebrew/bin/brew && "$(uname -m)" == arm64 ]]; then
  eval "$(/opt/homebrew/bin/brew shellenv zsh)"
elif [[ -x /usr/local/bin/brew ]]; then
  eval "$(/usr/local/bin/brew shellenv zsh)"
fi
typeset -U path PATH
path=("${XDG_DATA_HOME:-$HOME/.local/share}/mise/shims" "$HOME/.local/bin" "${CARGO_HOME:-$HOME/.cargo}/bin" "$HOME/.bun/bin" $path)
export PATH
