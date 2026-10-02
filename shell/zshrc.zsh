# Also works when the terminal opens a non-login interactive shell.
[[ -r "${XDG_CONFIG_HOME:-$HOME/.config}/mac-dev-bootstrap/zprofile.zsh" ]] && source "${XDG_CONFIG_HOME:-$HOME/.config}/mac-dev-bootstrap/zprofile.zsh"
[[ -o interactive ]] || return
# Avoid running integrations twice if .zshrc is re-sourced.
[[ ${MAC_DEV_BOOTSTRAP_INTERACTIVE_READY:-0} == 1 ]] && return
MAC_DEV_BOOTSTRAP_INTERACTIVE_READY=1
if (( $+commands[mise] )); then eval "$(mise activate zsh)"; fi
if (( ! $+functions[compdef] )); then autoload -Uz compinit && compinit; fi
if (( $+commands[fzf] )); then source <(fzf --zsh); fi
if (( $+commands[zoxide] )); then eval "$(zoxide init zsh)"; fi
if (( $+commands[atuin] )); then eval "$(atuin init zsh --disable-up-arrow)"; fi
if (( $+commands[wt] )); then eval "$(wt config shell init zsh)"; fi
if (( $+commands[omp] )); then eval "$(omp completions zsh)"; fi
# direnv is deliberately opt-in; mise owns the default environment.
# eval "$(direnv hook zsh)"
