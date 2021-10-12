# Hex display with python turtle

A simple program to draw decimal numbers as hexadecimals.
 - Digits are rendered from a font
 - A font is a directory with one svg file for each hexadecimal digit (`0.svg` ... `F.svg`)
 - Only a subset of the SVG spec is implemented
    - Only `<path>` tags are rendered
    - In the path tag's `d` attribute only the `m`/`M`, `l`/`L`, `h`/`H`, `v`/`V`, `z`/`Z` commands are supported
    - In the path tag's `d` attribute auto-separating doesn't work if there are two negative numbers after each other. Put a space or a comma in between
    - Transforms are not supported
 
 There are two fonts included:
  - segment - 16-segment like look. SVG files taken from [here](https://gitlab.com/zebulon-1er/text2svg/-/blob/master/text2svg.sh), credit to Frantz Balinski
  - roman - an attempt at imagining what roman hexadecimal numbers could look like. It wasn't the best idea but here it is
  
  ## Usage
  
  ```
  usage: display.py [-h] [-f FONT] [--scale SCALE] [--speed SPEED] [--debug-font]

optional arguments:
  -h, --help            show this help message and exit
  -f FONT, --font FONT  Path to a directory containing the font. The directory should contain an svg file for each hexadecimal digit plus an x.svg
                        file for the `x` symbol.
  --scale SCALE         Font scale
  --speed SPEED         Turtle speed
  --debug-font          Render all digits to test the font
```

To use the roman font:

```
python display.py -f roman
```
