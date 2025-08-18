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
# Run from GitHub - replace with your actual repo URL
uvx --from git+https://github.com/yourusername/rclone_explorer.git rclone-explorer --help

# With options
uvx --from git+https://github.com/yourusername/rclone_explorer.git rclone-explorer --max-items 20 my_remote:/my/path
```

### Install globally with uv

```bash
uv tool install git+https://github.com/yourusername/rclone_explorer.git

# Then run anywhere
rclone-explorer --help
```

### Direct script usage

```bash
./rclone_explorer.py --help
```

