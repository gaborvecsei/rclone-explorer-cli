# rclone Explorer

An ncdu-like interactive file browser for rclone cloud storage remotes.

## Features

- Navigate through rclone remotes interactively
- ncdu-style interface with keyboard navigation
- Shows file sizes in human-readable format
- Paginated view (configurable max items per directory)
- Directory navigation with breadcrumb support

## Requirements

- Python 3.6+
- rclone installed and configured
- Terminal with curses support

## Usage

```bash
# Basic usage - explore root of a remote
./rclone_explorer.py my_remote:

# Start from a specific path
./rclone_explorer.py my_remote:/path/to/folder

# Limit number of items shown per directory
./rclone_explorer.py --max-items 20 my_remote:

# Show help
./rclone_explorer.py --help
```

## Controls

- **↑/↓ Arrow Keys**: Navigate up/down through items
- **Enter**: Enter selected directory (does nothing for files)
- **b**: Go back to previous directory
- **q** or **Esc**: Quit

## Setup

1. Make sure rclone is installed and configured:
   ```bash
   rclone config
   ```

2. Make the script executable:
   ```bash
   chmod +x rclone_explorer.py
   ```

3. Run the explorer:
   ```bash
   ./rclone_explorer.py your_remote:
   ```

## Examples

```bash
# Browse Google Drive remote
./rclone_explorer.py gdrive:

# Browse specific folder in Dropbox
./rclone_explorer.py dropbox:/Photos

# Show more items per page
./rclone_explorer.py --max-items 25 s3bucket:
```