#!/usr/bin/env python3
import curses
import json
import subprocess
import sys
from contextlib import suppress


def rclone(cmd, path=""):
    with suppress(subprocess.CalledProcessError, json.JSONDecodeError):
        result = subprocess.run(["rclone"] + cmd + ([path] if path else []), capture_output=True, text=True, check=True)
        return result.stdout
    return ""


def exit_error(msg):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def safe_addstr(stdscr, y, x, text, attr=0):
    with suppress(curses.error):
        stdscr.addstr(y, x, text, attr)


class RcloneExplorer:

    def __init__(self, remote_path, max_items=10):
        self.remote_path, self.max_items = remote_path, max_items
        self.current_path, self.selected_index = "", 0
        self.items, self.path_stack = [], []

    def get_items(self, path=""):
        full_path = f"{self.remote_path}{path}" if path else self.remote_path
        data = rclone(["lsjson"], full_path)
        if data:
            items = json.loads(data)
            items.sort(key=lambda x: (not x.get("IsDir"), x["Name"].lower()))
            return items
        return []

    def format_size(self, size):
        if size == 0:
            return "0 B"
        for i, unit in enumerate(["B", "KB", "MB", "GB", "TB"]):
            if size < 1024**(i + 1) or i == 4:
                s = size / (1024**i)
                return f"{int(s)} {unit}" if i == 0 else f"{s:.1f} {unit}"

    def draw(self, stdscr):
        stdscr.clear()
        h, w = stdscr.getmaxyx()

        safe_addstr(stdscr, 0, 0, f"rclone: {self.remote_path}{self.current_path}"[:w - 1], curses.A_BOLD)
        safe_addstr(stdscr, 1, 0, "↑/↓: navigate  ENTER: open  b: back  q: quit")

        for i, item in enumerate(self.items[:self.max_items]):
            if 3 + i >= h - 1:
                break
            is_dir = item.get("IsDir")
            icon = "📁 " if is_dir else "📄 "
            size_str = "<DIR>" if is_dir else self.format_size(item.get("Size", 0))
            name = item["Name"]

            max_len = w - len(icon) - len(size_str) - 10
            if len(name) > max_len:
                name = name[:max_len - 3] + "..."

            line = f"{icon}{name:<{max_len}} {size_str:>8}"
            attr = curses.A_REVERSE if i == self.selected_index else 0
            safe_addstr(stdscr, 3 + i, 0, line[:w - 1], attr)

        if len(self.items) > self.max_items:
            safe_addstr(stdscr, 3 + min(len(self.items), self.max_items), 0,
                        f"... ({len(self.items) - self.max_items} more)")
        stdscr.refresh()

    def navigate(self, path):
        self.current_path, self.selected_index = path, 0
        self.items = self.get_items(path)

    def run(self, stdscr):
        curses.curs_set(0)
        stdscr.keypad(True)
        self.navigate("")

        while True:
            self.draw(stdscr)
            key = stdscr.getch()

            if key in (ord('q'), 27):
                break
            elif key == ord('b') and self.path_stack:
                self.navigate(self.path_stack.pop())
            elif key == curses.KEY_UP and self.selected_index > 0:
                self.selected_index -= 1
            elif key == curses.KEY_DOWN and self.selected_index < min(len(self.items) - 1, self.max_items - 1):
                self.selected_index += 1
            elif key in (curses.KEY_ENTER, 10, 13) and self.items and self.selected_index < len(self.items):
                item = self.items[self.selected_index]
                if item.get("IsDir"):
                    self.path_stack.append(self.current_path)
                    self.navigate(f"{self.current_path}/{item['Name']}".lstrip("/"))


def main():
    if not rclone(["version"]):
        exit_error("rclone not found")

    remote = sys.argv[1] if len(sys.argv) > 1 else None
    if not remote:
        data = rclone(["listremotes"])
        remotes = [line.strip() for line in data.splitlines() if line.strip()] if data else []
        if not remotes:
            exit_error("No remotes found. Run 'rclone config'")

        print("Available remotes:")
        for i, r in enumerate(remotes):
            print(f"{i+1}: {r.rstrip(':')}")
        try:
            remote = remotes[int(input("Select remote: ")) - 1]
        except (ValueError, IndexError):
            exit_error("Invalid selection")

    if ":" not in remote:
        remote += ":"

    try:
        curses.wrapper(RcloneExplorer(remote).run)
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        exit_error(str(e))


if __name__ == "__main__":
    main()
