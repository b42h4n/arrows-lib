# Arrows.py
Simple python lib to work with http://logic-arrows.io

## GUI editor

The Tkinter editor lets you draw arrows on a scrollable grid, set their
direction and properties, and import or export maps in the library's encoded
format. Right-click a cell to sample its properties.

Run it from the repository root with Python 3:

```sh
PYTHONPATH=src python -m arrows.editor
```

Use the **Код карты** field to import or export an encoded map, or use the file
buttons to open and save `.txt` maps. The editor uses Tkinter, which is included
with most Python installations.
