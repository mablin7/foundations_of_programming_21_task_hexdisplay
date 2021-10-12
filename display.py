#!/usr/bin/env python3
import re, string, argparse
from typing import Optional, List, Dict, Tuple
from pathlib import Path
from dataclasses import dataclass
from xml.dom import minidom
from turtle import TurtleScreen, Screen, RawTurtle, Vec2D


@dataclass
class PathCommand:
    """ Stores a single path command, in a generic form """
    is_abs: bool
    pendown: bool
    x: Optional[float] = None
    y: Optional[float] = None


class PathDrawer:
    """ Parses and draws an SVG <path> with the given turtle
        
    Only supports m/M, l/L, v/V, h/H, z/Z path commands
    """
    PATH_D_PAT = r"(?P<cmd>[a-zA-Z])(?P<params> ?(?:-?[\d\.e-]+[, ]?)+)?"

    def __init__(self, turtle: RawTurtle, path_d: str, scale: float = 1):
        self.t = turtle

        self.commands: List[PathCommand] = []
        for cmd, params_str in re.findall(self.PATH_D_PAT, path_d):
            groups = params_str.strip().split(" ")
            all_params = [ float(p) * scale for group in groups for p in re.split("[, ]", group) if p != "" ]
            param_groups = [[]]
            for p in all_params:
                if len(param_groups[-1]) < 2:
                    param_groups[-1].append(p)
                else:
                    param_groups.append([p])

            # First command needs to be absolute
            normalized_cmd = cmd # so we don't modify the original command
            if len(self.commands) == 0:
                normalized_cmd = cmd.upper()    
            self._add_command(normalized_cmd, param_groups.pop(0))

            # Some commands have implicit follow-up commands, need to insert them
            if len(param_groups) > 0:
                implicit_cmd = "l" if cmd == "m" else "L" if cmd == "M" else cmd
                for group in param_groups:
                    self._add_command(implicit_cmd, group)

    def _add_command(self, cmd: str, params: List[float]):
        cmd_type = cmd.lower()
        is_abs = cmd.isupper()
        pendown = cmd_type != "m"
        x = params[0] if len(params) > 0 and cmd_type != "v" else None
        y = params[1] if len(params) > 1 else params[0] if cmd_type == "v" else None
        y = -y if y is not None else None # SVG uses a top left coordinate system , we'll use a bottom left, so we just negate y
        new_cmd = PathCommand(is_abs, pendown, x, y)
        self.commands.append(new_cmd)

    def draw(self, offset: Vec2D = (0, 0)) -> float:
        """ Draws the path.

        Returns the rightmost point of the path for determining where to start the next digit.
        """
        first_point: Optional[Tuple[float, float]] = None
        max_x = self.commands[-1].y
        for cmd in self.commands:
            if cmd.pendown:
                self.t.pendown()
                if first_point is None:
                    first_point = self.t.pos()
            else:
                self.t.penup()

            if cmd.x is None and cmd.y is None:
                # Both coordinates none -> close path
                self.t.goto(first_point or (0, 0))
                first_point = None
            elif cmd.y is None:
                # Only Y is none -> vertical line
                x = cmd.x + offset[0] if cmd.is_abs else cmd.x + self.t.xcor() # type: ignore # Pyright can't follow the logic
                self.t.setx(x)
            elif cmd.x is None:
                # Only X is none -> horizontal line
                y = cmd.y + offset[1] if cmd.is_abs else cmd.y + self.t.ycor()
                self.t.sety(y)
            else:
                # Neither is none -> line
                x = cmd.x + offset[0] if cmd.is_abs else cmd.x + self.t.xcor()
                y = cmd.y + offset[1] if cmd.is_abs else cmd.y + self.t.ycor()
                self.t.goto(x, y)

            if max_x is None or self.t.xcor() > max_x:
                max_x = self.t.xcor()
        return max_x or 0


class DigitDisplay:
    """Parses and draws all paths contained in a digit."""
    def __init__(self, font_path: Path, turtle: RawTurtle, scale: float = 1):
        doc = minidom.parse(str(font_path))
        path_d_strings = [path.getAttribute('d') for path in doc.getElementsByTagName('path')]
        doc.unlink()
        self.paths = [ PathDrawer(turtle, d, scale) for d in path_d_strings ]
        self.next_y = None

    def draw(self, x_offset: float = 0, global_offset: Vec2D = (0, 0)) -> float:
        """Draws the digit at the given offset.

        Returns the x value where the next digit can be started.
        """
        max_x = None
        for path in self.paths:
            x = path.draw((x_offset, global_offset[1]))
            if max_x is None or x > max_x:
                max_x = x
        return max_x or 0


class DigitsDisplay:
    """Draws multiple consecutive digits."""
    DIGIT_CHARS = [c for c in string.hexdigits if not c.islower()] + ['x']
    DIGIT_MARGIN = 10

    def __init__(self, font_dir: Path, screen: TurtleScreen, scale: float = 1, speed: int = 0):
        self.t = RawTurtle(screen)
        self.speed = speed
        self.scale = scale
        self.digit_drawers: Dict[str, DigitDisplay] = {}
        for char in self.DIGIT_CHARS:
            font_file = font_dir / f"{char}.svg"
            self.digit_drawers[char] = DigitDisplay(font_file, self.t, scale)

    def draw(self, digits_str: str, offset: Vec2D = (0, 0)):
        """Clear the display ad draw the given string"""
        self.t.reset()
        self.t.speed(self.speed)
        self.t.hideturtle()
        x_offset = offset[0]
        for digit in digits_str:
            if digit not in self.digit_drawers:
                if digit.upper() not in self.digit_drawers:
                    raise ValueError(f"{digit} is an invalid hex digit!")
                digit = digit.upper()
            x_offset = self.digit_drawers[digit].draw(x_offset) + self.DIGIT_MARGIN


if __name__ == "__main__":
    # Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--font", type=str, default="segment", help="Path to a directory containing the font. The directory should contain an svg file for each hexadecimal digit plus an x.svg file for the `x` symbol.")
    parser.add_argument("--scale", type=int, help="Font scale", default=5)
    parser.add_argument("--speed", type=int, help="Turtle speed", default=0)
    parser.add_argument("--debug-font", help="Render all digits to test the font", action='store_true')
    args = parser.parse_args()
    font_dir = Path(args.font)
    if not font_dir.exists():
        raise FileNotFoundError(f"{font_dir} not found")

    # Init screen
    screen = Screen()
    x_start = -(screen.window_width() / 2) + 20
    display = DigitsDisplay(font_dir, screen, scale=args.scale, speed=args.speed)

    if args.debug_font:
        display.draw(''.join(display.DIGIT_CHARS), offset=(x_start, 0))
        screen.mainloop()
    else:
        # Main loop
        while True:
            n = screen.numinput("Input number", "Type in a number to be converted: ")
            if n is None:
                break
            n_hex_str = hex(int(n))
            display.draw(n_hex_str, offset=(x_start, 0))
