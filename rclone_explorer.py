import argparse
import curses
import json
import subprocess
import sys
from contextlib import suppress
from dataclasses import dataclass
from pathlib import PurePath
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class RcloneItem:
    name: str
    size: int
    is_dir: bool
    mod_time: str = ""

    def __repr__(self) -> str:
        return f"RcloneItem({self.name}, {self.size}, {self.is_dir})"


class RcloneExplorer:
    # Constants
    FOLDER_ICON = "📁 "
    FILE_ICON = "📄 "
    QUIT_KEYS = {ord('q'), 27}    # 'q' or ESC
    ENTER_KEYS = {curses.KEY_ENTER, 10, 13}

    def __init__(self, remote_path: str, max_items: int = 10):
        self.remote_path: str = remote_path
        self.current_path: str = ""
        self.max_items: int = max_items
        self.items: List[RcloneItem] = []
        self.selected_index: int = 0
        self.path_stack: List[str] = []

    def get_remote_items(self, path: str = "") -> List[RcloneItem]:
        full_path = str(PurePath(self.remote_path) / path) if path else self.remote_path

        with suppress(subprocess.CalledProcessError, json.JSONDecodeError):
            result = subprocess.run(["rclone", "lsjson", full_path], capture_output=True, text=True, check=True)
            json_data = json.loads(result.stdout)

            items = [
                RcloneItem(name=item["Name"],
                           size=item.get("Size", 0),
                           is_dir=item.get("IsDir", False),
                           mod_time=item.get("ModTime", "")) for item in json_data
            ]

            items.sort(key=lambda x: (not x.is_dir, x.name.lower()))
            return items

        return []

    def format_size(self, size_bytes: int) -> str:
        if size_bytes == 0:
            return "0 B"

        units = ["B", "KB", "MB", "GB", "TB"]
        for i, unit in enumerate(units):
            if size_bytes < 1024**(i + 1) or i == len(units) - 1:
                size = size_bytes / (1024**i)
                return f"{int(size)} {unit}" if i == 0 else f"{size:.1f} {unit}"

    def draw_header(self, stdscr, width: int):
        """Draw the title and navigation info."""
        title = f"rclone explorer - {self.remote_path}{self.current_path}"
        stdscr.addstr(0, 0, title[:width - 1], curses.A_BOLD)

        nav_info = "Press ENTER to open, 'q' to quit, 'b' to go back"
        if len(nav_info) < width:
            stdscr.addstr(1, 0, nav_info)

    def draw_items(self, stdscr, width: int, height: int, start_row: int):
        """Draw the file/folder items."""
        items_to_show = self.items[:self.max_items]

        for i, item in enumerate(items_to_show):
            if start_row + i >= height - 1:
                break

            prefix = self.FOLDER_ICON if item.is_dir else self.FILE_ICON
            size_str = self.format_size(item.size) if not item.is_dir else "<DIR>"

            max_name_len = width - len(prefix) - len(size_str) - 10
            name = item.name
            if len(name) > max_name_len:
                name = name[:max_name_len - 3] + "..."

            line = f"{prefix}{name:<{max_name_len}} {size_str:>10}"
            attr = curses.A_REVERSE if i == self.selected_index else curses.A_NORMAL

            with suppress(curses.error):
                stdscr.addstr(start_row + i, 0, line[:width - 1], attr)

    def draw_more_indicator(self, stdscr, start_row: int, items_shown: int):
        """Draw indicator for additional items."""
        if len(self.items) > self.max_items:
            more_text = f"... ({len(self.items) - self.max_items} more items)"
            with suppress(curses.error):
                stdscr.addstr(start_row + items_shown, 0, more_text, curses.A_DIM)

    def draw_screen(self, stdscr):
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        self.draw_header(stdscr, width)

        start_row = 3
        self.draw_items(stdscr, width, height, start_row)

        items_shown = min(len(self.items), self.max_items)
        self.draw_more_indicator(stdscr, start_row, items_shown)

        stdscr.refresh()

    def navigate_to(self, path: str):
        self.current_path = path
        self.items = self.get_remote_items(path)
        self.selected_index = 0

    def go_back(self):
        if self.path_stack:
            previous_path = self.path_stack.pop()
            self.navigate_to(previous_path)

    def enter_selected(self):
        if not self.items or self.selected_index >= len(self.items):
            return

        selected_item = self.items[self.selected_index]
        if selected_item.is_dir:
            self.path_stack.append(self.current_path)
            new_path = str(PurePath(self.current_path) / selected_item.name).lstrip("/")
            self.navigate_to(new_path)

    def handle_key(self, key: int) -> bool:
        """Handle key input. Returns False to quit, True to continue."""
        if key in self.QUIT_KEYS:
            return False
        elif key == ord('b') and self.path_stack:
            self.go_back()
        elif key == curses.KEY_UP and self.selected_index > 0:
            self.selected_index -= 1
        elif key == curses.KEY_DOWN and self.selected_index < min(len(self.items) - 1, self.max_items - 1):
            self.selected_index += 1
        elif key in self.ENTER_KEYS:
            self.enter_selected()
        return True

    def run(self, stdscr):
        curses.curs_set(0)
        stdscr.keypad(True)

        self.navigate_to("")

        while True:
            self.draw_screen(stdscr)
            key = stdscr.getch()
            if not self.handle_key(key):
                break


def check_rclone() -> bool:
    with suppress(subprocess.CalledProcessError, FileNotFoundError):
        subprocess.run(["rclone", "version"], capture_output=True, check=True)
        return True
    return False


def get_available_remotes() -> List[str]:
    with suppress(subprocess.CalledProcessError):
        result = subprocess.run(["rclone", "listremotes"], capture_output=True, text=True, check=True)
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return []


def select_remote_interactive() -> Optional[str]:
    remotes = get_available_remotes()

    if not remotes:
        print("No rclone remotes found. Please configure remotes with 'rclone config'.", file=sys.stderr)
        return None

    def remote_selector(stdscr):
        curses.curs_set(0)
        stdscr.keypad(True)
        selected_index = 0

        while True:
            stdscr.clear()
            height, width = stdscr.getmaxyx()

            title = "Select rclone remote:"
            stdscr.addstr(0, 0, title, curses.A_BOLD)

            instructions = "Use arrow keys to navigate, ENTER to select, 'q' to quit"
            stdscr.addstr(1, 0, instructions)

            start_row = 3
            for i, remote in enumerate(remotes):
                if start_row + i >= height - 1:
                    break

                display_name = remote.rstrip(':')
                attr = curses.A_REVERSE if i == selected_index else curses.A_NORMAL

                try:
                    stdscr.addstr(start_row + i, 2, f"{display_name}", attr)
                except curses.error:
                    pass

            stdscr.refresh()

            key = stdscr.getch()

            if key == ord('q') or key == 27:
                return None
            elif key == curses.KEY_UP and selected_index > 0:
                selected_index -= 1
            elif key == curses.KEY_DOWN and selected_index < len(remotes) - 1:
                selected_index += 1
            elif key == curses.KEY_ENTER or key == 10 or key == 13:
                return remotes[selected_index]

    return curses.wrapper(remote_selector)


def parse_remote_path(remote_arg: str) -> str:
    if not remote_arg:
        raise ValueError("Remote path cannot be empty")

    return remote_arg if ":" in remote_arg else f"{remote_arg}:"


def main():
    parser = argparse.ArgumentParser(description="rclone explorer - An ncdu-like explorer for rclone storages",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog="""
Examples:
  rclone_explorer.py my_storage:
  rclone_explorer.py my_storage:/backup/Media
  rclone_explorer.py --max-items 20 my_storage:/docs
        """)

    parser.add_argument(
        "remote",
        nargs='?',
        help=
        "Remote storage and optional path (e.g., 'my_storage:' or 'my_storage:/backup/Media'). If not provided, you'll be prompted to select from available remotes."
    )

    parser.add_argument("--max-items",
                        "-m",
                        type=int,
                        default=10,
                        help="Maximum number of items to show per directory (default: 10)")

    args = parser.parse_args()

    if not check_rclone():
        print("Error: rclone command not found. Please install rclone first.", file=sys.stderr)
        sys.exit(1)

    try:
        if args.remote is None:
            selected_remote = select_remote_interactive()
            if selected_remote is None:
                print("No remote selected. Exiting.")
                sys.exit(0)
            remote_path = selected_remote
        else:
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
