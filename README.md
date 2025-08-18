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

```bash
# Show help
./rclone_explorer.py --help

# Basic usage - explore root of a remote
./rclone_explorer.py my_remote:

# Start from a specific path
./rclone_explorer.py my_remote:/path/to/folder

# Limit number of items shown per directory (not to overcrowd the terminal)
./rclone_explorer.py --max-items 20 my_remote:
```

