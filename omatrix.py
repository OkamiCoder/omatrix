#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import curses
import random
import time

KATAKANA = [chr(c) for c in range(0xFF66, 0xFF9D)]          
EXTRA    = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ<>|/\\=+-*:."
ALPHABET = KATAKANA + list(EXTRA)

GREEN_LEVELS = [231, 46, 40, 34, 28, 22]                   
BASIC_COLORS = {
    "green":   curses.COLOR_GREEN,
    "red":     curses.COLOR_RED,
    "blue":    curses.COLOR_BLUE,
    "cyan":    curses.COLOR_CYAN,
    "magenta": curses.COLOR_MAGENTA,
    "yellow":  curses.COLOR_YELLOW,
    "white":   curses.COLOR_WHITE,
}


def build_levels(color_name: str, has_256: bool):
    if color_name == "green" and has_256:
        return GREEN_LEVELS
    base = BASIC_COLORS.get(color_name, curses.COLOR_GREEN)
    return [curses.COLOR_WHITE, base, base, base, base, base]


def init_colors(color_name: str) -> int:
    curses.start_color()
    try:
        curses.use_default_colors()                       
    except curses.error:
        pass
    levels = build_levels(color_name, curses.COLORS >= 256)
    for i, col in enumerate(levels):
        try:
            curses.init_pair(i + 1, col, -1)
        except curses.error:
            curses.init_pair(i + 1, col, curses.COLOR_BLACK)
    return len(levels)


class Column:
    __slots__ = ("x", "head", "trail", "speed", "counter", "cells")

    def __init__(self, x, height, speed_lo, speed_hi):
        self.x = x
        self.head = 0
        self.trail = 0
        self.speed = 1
        self.counter = 0
        self.cells = {}                                      
        self.reset(height, speed_lo, speed_hi)

    def reset(self, height, speed_lo, speed_hi):
        self.head    = random.randint(-height, 0)           
        max_trail    = max(6, min(30, height - 1))
        self.trail   = random.randint(6, max_trail)
        self.speed   = random.randint(speed_lo, speed_hi)
        self.counter = random.randint(0, self.speed - 1)
        self.cells.clear()

    def step(self, height, speed_lo, speed_hi):
        self.counter += 1
        if self.counter < self.speed:
            return
        self.counter = 0
        self.head += 1
        self.cells[self.head] = random.choice(ALPHABET)

        cutoff = self.head - self.trail
        for y in [y for y in self.cells if y < cutoff]:
            del self.cells[y]

        if cutoff > height:
            self.reset(height, speed_lo, speed_hi)

    def draw(self, stdscr, height, n_levels):
        head, trail, x = self.head, self.trail, self.x
        for y, ch in self.cells.items():
            if y < 0 or y >= height:
                continue
            dist = head - y
            if dist < 0:
                continue
            lvl = min(n_levels - 1, dist * n_levels // (trail + 1))
            attr = curses.color_pair(lvl + 1)
            if dist == 0:
                attr |= curses.A_BOLD
            try:
                stdscr.addstr(y, x, ch, attr)
            except curses.error:
                pass                                      


def run(stdscr, args):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)

    n_levels = init_colors(args.color)

    speed_lo = max(1, args.speed)
    speed_hi = speed_lo + 3

    height, width = stdscr.getmaxyx()
    columns = [Column(x, height, speed_lo, speed_hi) for x in range(width)]

    frame_time = 1.0 / max(1, args.fps)
    paused = False

    while True:
        ch = stdscr.getch()
        if ch in (ord('q'), ord('Q'), 27):
            break
        elif ch == ord(' '):
            paused = not paused
        elif ch in (ord('+'), ord('=')):
            speed_lo = max(1, speed_lo - 1)
            speed_hi = speed_lo + 3
        elif ch in (ord('-'), ord('_')):
            speed_lo += 1
            speed_hi = speed_lo + 3

        new_h, new_w = stdscr.getmaxyx()
        if new_h != height or new_w != width:
            height, width = new_h, new_w
            columns = [Column(x, height, speed_lo, speed_hi) for x in range(width)]

        if not paused:
            stdscr.erase()
            for col in columns:
                col.step(height, speed_lo, speed_hi)
                col.draw(stdscr, height, n_levels)
            stdscr.refresh()

        time.sleep(frame_time)


def parse_args():
    p = argparse.ArgumentParser(description="Matrix digital rain")
    p.add_argument("-c", "--color", default="green",
                   choices=list(BASIC_COLORS.keys()),
                   help="цвет дождя (по умолчанию green)")
    p.add_argument("-s", "--speed", type=int, default=4,
                   help="базовая скорость: меньше — быстрее (по умолчанию 4)")
    p.add_argument("-f", "--fps", type=int, default=60,
                   help="кадров в секунду (по умолчанию 60)")
    return p.parse_args()


def main():
    args = parse_args()
    try:
        curses.wrapper(run, args)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
