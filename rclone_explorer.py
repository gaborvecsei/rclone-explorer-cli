#!/usr/bin/env python3
"""
rclone_explorer - An ncdu-like explorer for rclone storages
"""

import argparse
import curses
import json
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple


class RcloneItem:
    """Represents a file or directory from rclone"""

    def __init__(self, name: str, size: int, is_dir: bool, mod_time: str = ""):
        self.name: str = name
        self.size: int = size
        self.is_dir: bool = is_dir
        self.mod_time: str = mod_time

    def __repr__(self) -> str:
        return f"RcloneItem({self.name}, {self.size}, {self.is_dir})"


class RcloneExplorer:
    """Main rclone explorer class"""

    def __init__(self, remote_path: str, max_items: int = 10):
        self.remote_path: str = remote_path
        self.current_path: str = ""
        self.max_items: int = max_items
        self.items: List[RcloneItem] = []
        self.selected_index: int = 0
        self.path_stack: List[str] = []

    def get_remote_items(self, path: str = "") -> List[RcloneItem]:
        """Get items from rclone ls command"""
        full_path = f"{self.remote_path}{path}"

        try:
            # Use rclone lsjson for detailed information
            result = subprocess.run(["rclone", "lsjson", full_path], capture_output=True, text=True, check=True)

            items = []
            json_data = json.loads(result.stdout)

            for item in json_data:
                is_dir = item.get("IsDir", False)
                name = item["Name"]
                size = item.get("Size", 0)
                mod_time = item.get("ModTime", "")

                items.append(RcloneItem(name, size, is_dir, mod_time))

            # Sort: directories first, then by name
            items.sort(key=lambda x: (not x.is_dir, x.name.lower()))

            return items

        except subprocess.CalledProcessError as e:
            return []
        except json.JSONDecodeError:
            return []

    def format_size(self, size_bytes: int) -> str:
        """Format size in human readable format"""
        if size_bytes == 0:
            return "0 B"

        units = ["B", "KB", "MB", "GB", "TB"]
        unit_index = 0
        size = float(size_bytes)

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.1f} {units[unit_index]}"

    def draw_screen(self, stdscr):
        """Draw the main screen"""
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Title
        title = f"rclone explorer - {self.remote_path}{self.current_path}"
        stdscr.addstr(0, 0, title[:width - 1], curses.A_BOLD)

        # Navigation info
        nav_info = "Press ENTER to open, 'q' to quit, 'b' to go back"
        if len(nav_info) < width:
            stdscr.addstr(1, 0, nav_info)

        # Items
        start_row = 3
        items_to_show = self.items[:self.max_items]

        for i, item in enumerate(items_to_show):
            if start_row + i >= height - 1:
                break

            # Format the line
            prefix = "📁 " if item.is_dir else "📄 "
            size_str = self.format_size(item.size) if not item.is_dir else "<DIR>"

            # Truncate name if too long
            max_name_len = width - len(prefix) - len(size_str) - 10
            name = item.name
            if len(name) > max_name_len:
                name = name[:max_name_len - 3] + "..."

            line = f"{prefix}{name:<{max_name_len}} {size_str:>10}"

            # Highlight selected item
            attr = curses.A_REVERSE if i == self.selected_index else curses.A_NORMAL

            try:
                stdscr.addstr(start_row + i, 0, line[:width - 1], attr)
            except curses.error:
                pass

        # Show "more items" indicator
        if len(self.items) > self.max_items:
            more_text = f"... ({len(self.items) - self.max_items} more items)"
            try:
                stdscr.addstr(start_row + len(items_to_show), 0, more_text, curses.A_DIM)
            except curses.error:
                pass

        stdscr.refresh()

    def navigate_to(self, path: str):
        """Navigate to a specific path"""
        self.current_path = path
        self.items = self.get_remote_items(path)
        self.selected_index = 0

    def go_back(self):
        """Go back to previous directory"""
        if self.path_stack:
            previous_path = self.path_stack.pop()
            self.navigate_to(previous_path)

    def enter_selected(self):
        """Enter the selected directory"""
        if not self.items or self.selected_index >= len(self.items):
            return

        selected_item = self.items[self.selected_index]

        # Only navigate into directories
        if selected_item.is_dir:
            # Save current path to stack
            self.path_stack.append(self.current_path)

            # Navigate to new path
            new_path = f"{self.current_path}/{selected_item.name}" if self.current_path else selected_item.name
            new_path = new_path.lstrip("/")    # Remove leading slash
            self.navigate_to(new_path)

    def run(self, stdscr):
        """Main application loop"""
        # Setup curses
        curses.curs_set(0)    # Hide cursor
        stdscr.keypad(True)

        # Load initial items
        self.navigate_to("")

        while True:
            self.draw_screen(stdscr)

            # Get user input
            key = stdscr.getch()

            if key == ord('q') or key == 27:    # 'q' or ESC
                break
            elif key == ord('b') and self.path_stack:    # 'b' for back
                self.go_back()
            elif key == curses.KEY_UP and self.selected_index > 0:
                self.selected_index -= 1
            elif key == curses.KEY_DOWN and self.selected_index < min(len(self.items) - 1, self.max_items - 1):
                self.selected_index += 1
            elif key == curses.KEY_ENTER or key == 10 or key == 13:    # Enter
                self.enter_selected()


def check_rclone() -> bool:
    """Check if rclone is available"""
    try:
        subprocess.run(["rclone", "version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def parse_remote_path(remote_arg: str) -> str:
    """Parse and validate remote path argument"""
    if not remote_arg:
        raise ValueError("Remote path cannot be empty")

    # Ensure it ends with colon if no path specified
    if ":" not in remote_arg:
        remote_arg += ":"

    return remote_arg


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="rclone explorer - An ncdu-like explorer for rclone storages",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog="""
Examples:
  rclone_explorer.py my_storage:
  rclone_explorer.py my_storage:/backup/Media
  rclone_explorer.py --max-items 20 my_storage:/docs
        """)

    parser.add_argument("remote",
                        help="Remote storage and optional path (e.g., 'my_storage:' or 'my_storage:/backup/Media')")

    parser.add_argument("--max-items",
                        "-m",
                        type=int,
                        default=10,
                        help="Maximum number of items to show per directory (default: 10)")

    args = parser.parse_args()

    # Check if rclone is available
    if not check_rclone():
        print("Error: rclone command not found. Please install rclone first.", file=sys.stderr)
        sys.exit(1)

    try:
        remote_path = parse_remote_path(args.remote)
        explorer = RcloneExplorer(remote_path, args.max_items)
        curses.wrapper(explorer.run)
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
