# rclone Explorer

A command line interface to quickly view remote contents for rclone remotes.

> Why? 

I needed a lightweight tool with which I can easily browse my configured remotes. 

## Features

- Navigate through rclone remotes interactively
- Shows file sizes in human-readable format
- Directory navigation with breadcrumb support

## Requirements

- Python 3.6+
- `rclone` installed and configured
- Terminal with `curses` support

## Usage

### Run directly with uvx (no installation needed)

```bash
# Run from GitHub
uvx --from git+https://github.com/gaborvecsei/rclone-explorer-cli.git rclone-explorer my_remote:

# With options
uvx --from git+https://github.com/gaborvecsei/rclone-explorer-cli.git rclone-explorer --max-items 20 my_remote:
```

### Install globally with uv

```bash
uv tool install git+https://github.com/gaborvecsei/rclone-explorer-cli.git

# Then run anywhere
rclone-explorer my_remote:
```

### Direct script usage

```bash
./rclone_explorer.py my_remote:
```

