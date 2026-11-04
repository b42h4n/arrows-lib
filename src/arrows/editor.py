import binascii
import copy
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import zlib

from .arrows import Arrow, ArrowType, Color, Direction, Letter, Map


CELL_SIZE = 44
INITIAL_MIN = -128
INITIAL_MAX = 127

_DIRECTION_GLYPHS = ("↑", "→", "↓", "←")
_COLOR_HEX = {
    Color.White: "#ffffff",
    Color.Red: "#f4a6a6",
    Color.Blue: "#a9c8f2",
    Color.Yellow: "#f6e69b",
    Color.Green: "#a9d8ae",
    Color.Orange: "#f4c18c",
    Color.Purple: "#ccb3e5",
    Color.Black: "#999999",
}

_KEY_ACTIONS = {
    "w": "up", "cyrillic_tse": "up",
    "d": "right", "cyrillic_ve": "right",
    "s": "down", "cyrillic_yeru": "down",
    "a": "left", "cyrillic_ef": "left",
    "e": "select", "cyrillic_u": "select",
    "c": "copy", "cyrillic_es": "copy",
    "v": "paste", "cyrillic_em": "paste",
    "x": "cut", "cyrillic_che": "cut",
    "backspace": "delete", "delete": "delete",
    "escape": "cancel",
}
_DIRECTION_INDEX = {"up": 0, "right": 1, "down": 2, "left": 3}


def _short_type(arrow_type: ArrowType) -> str:
    if arrow_type == ArrowType.Empty:
        return ""
    words = []
    current = ""
    for character in arrow_type.name:
        if character.isupper() and current:
            words.append(current)
            current = character
        else:
            current += character
    if current:
        words.append(current)
    if len(words) > 1:
        return "".join(word[0] for word in words)[:4].upper()
    return arrow_type.name[:4]


class ArrowEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Arrows Map Editor")
        self.geometry("1040x760")
        self.minsize(760, 560)

        self.map = Map()
        self.map.version = 5
        self.min_x = INITIAL_MIN
        self.max_x = INITIAL_MAX
        self.min_y = INITIAL_MIN
        self.max_y = INITIAL_MAX
        self.last_position = None
        self.hover_position = None

        self.selection = None
        self.select_mode = False
        self.select_anchor = None
        self.clipboard = None

        self.type_var = tk.StringVar(value=ArrowType.Arrow.name)
        self.direction_var = tk.StringVar(value=Direction.North.name)
        self.flipped_var = tk.BooleanVar(value=False)
        self.color_var = tk.StringVar(value=Color.White.name)
        self.bright_var = tk.BooleanVar(value=False)
        self.letter_var = tk.StringVar(value=Letter.Empty.name)
        self.string_var = tk.StringVar()
        self.encoded_var = tk.StringVar()
        self.version_var = tk.StringVar(value="5")
        self.status_var = tk.StringVar(
            value="WASD — направление, E — выделение, C/V/X — копировать/вставить/вырезать, Backspace — удалить."
        )

        self._build_ui()
        self.bind("<Control-o>", lambda _event: self.open_file())
        self.bind("<Control-s>", lambda _event: self.save_file())
        self.bind("<Control-e>", lambda _event: self.export_map())
        self.bind("<Key>", self._on_key)
        self.after_idle(self._center_view)
        self.after_idle(self.canvas.focus_set)

    def _build_ui(self):
        controls = ttk.Frame(self, padding=(8, 8, 8, 4))
        controls.pack(fill=tk.X)

        ttk.Label(controls, text="Тип").grid(row=0, column=0, sticky="w")
        type_box = ttk.Combobox(
            controls,
            textvariable=self.type_var,
            values=[item.name for item in ArrowType],
            state="readonly",
            width=25,
        )
        type_box.grid(row=1, column=0, padx=(0, 8), sticky="ew")

        ttk.Label(controls, text="Направление").grid(row=0, column=1, sticky="w")
        direction_box = ttk.Combobox(
            controls,
            textvariable=self.direction_var,
            values=[item.name for item in Direction],
            state="readonly",
            width=11,
        )
        direction_box.grid(row=1, column=1, padx=(0, 8), sticky="ew")

        ttk.Checkbutton(controls, text="Отразить", variable=self.flipped_var).grid(
            row=1, column=2, padx=(0, 8), sticky="w"
        )

        ttk.Label(controls, text="Цвет").grid(row=0, column=3, sticky="w")
        color_box = ttk.Combobox(
            controls,
            textvariable=self.color_var,
            values=[item.name for item in Color],
            state="readonly",
            width=10,
        )
        color_box.grid(row=1, column=3, padx=(0, 8), sticky="ew")

        ttk.Checkbutton(controls, text="Яркий", variable=self.bright_var).grid(
            row=1, column=4, padx=(0, 8), sticky="w"
        )

        ttk.Label(controls, text="Буква").grid(row=0, column=5, sticky="w")
        letter_box = ttk.Combobox(
            controls,
            textvariable=self.letter_var,
            values=[item.name for item in Letter],
            state="readonly",
            width=9,
        )
        letter_box.grid(row=1, column=5, sticky="ew")

        for box in (type_box, direction_box, color_box, letter_box):
            box.bind("<<ComboboxSelected>>", lambda _e: self.canvas.focus_set())

        ttk.Label(controls, text="Строковые данные").grid(
            row=2, column=0, pady=(8, 0), sticky="w"
        )
        ttk.Entry(controls, textvariable=self.string_var).grid(
            row=3, column=0, columnspan=6, pady=(0, 4), sticky="ew"
        )
        controls.columnconfigure(0, weight=1)

        workspace = ttk.Frame(self, padding=(8, 4, 8, 4))
        workspace.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(
            workspace,
            background="#f5f6f8",
            highlightthickness=1,
            highlightbackground="#aeb4bd",
            takefocus=True,
        )
        horizontal = ttk.Scrollbar(
            workspace, orient=tk.HORIZONTAL, command=self._scroll_x
        )
        vertical = ttk.Scrollbar(
            workspace, orient=tk.VERTICAL, command=self._scroll_y
        )
        self.canvas.configure(
            xscrollcommand=horizontal.set,
            yscrollcommand=vertical.set,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        workspace.rowconfigure(0, weight=1)
        workspace.columnconfigure(0, weight=1)

        self.canvas.bind("<Configure>", lambda _event: self._draw_grid())
        self.canvas.bind("<Button-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<Button-3>", self._sample_cell)
        self.canvas.bind("<Motion>", self._show_coordinates)
        self.canvas.bind("<MouseWheel>", self._mouse_wheel)
        self.canvas.bind("<Button-4>", lambda _event: self._scroll_y("scroll", -1, "units"))
        self.canvas.bind("<Button-5>", lambda _event: self._scroll_y("scroll", 1, "units"))

        encoded = ttk.Frame(self, padding=(8, 4, 8, 4))
        encoded.pack(fill=tk.X)
        ttk.Label(encoded, text="Код карты").pack(anchor="w")
        ttk.Entry(encoded, textvariable=self.encoded_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8)
        )
        ttk.Button(encoded, text="Импорт", command=self.import_map).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Button(encoded, text="Экспорт", command=self.export_map).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Button(encoded, text="Копировать", command=self.copy_export).pack(
            side=tk.LEFT
        )

        file_buttons = ttk.Frame(self, padding=(8, 4, 8, 4))
        file_buttons.pack(fill=tk.X)
        ttk.Label(file_buttons, text="Версия").pack(side=tk.LEFT, padx=(0, 4))
        version_box = ttk.Combobox(
            file_buttons,
            textvariable=self.version_var,
            values=("0", "4", "5"),
            state="readonly",
            width=3,
        )
        version_box.pack(side=tk.LEFT, padx=(0, 8))
        version_box.bind("<<ComboboxSelected>>", self._change_version)
        ttk.Button(file_buttons, text="Открыть файл", command=self.open_file).pack(
            side=tk.LEFT, padx=(0, 4)
        )
        ttk.Button(file_buttons, text="Сохранить файл", command=self.save_file).pack(
            side=tk.LEFT
        )
        ttk.Label(file_buttons, textvariable=self.status_var).pack(
            side=tk.RIGHT, padx=4
        )

    def _center_view(self):
        self.canvas.configure(
            scrollregion=(
                0,
                0,
                (self.max_x - self.min_x + 1) * CELL_SIZE,
                (self.max_y - self.min_y + 1) * CELL_SIZE,
            )
        )
        self.canvas.xview_moveto(0.5)
        self.canvas.yview_moveto(0.5)
        self._draw_grid()

    def _scroll_x(self, *args):
        self.canvas.xview(*args)
        self._draw_grid()

    def _scroll_y(self, *args):
        self.canvas.yview(*args)
        self._draw_grid()

    def _visible_coordinates(self):
        left = max(0, int(self.canvas.canvasx(0) // CELL_SIZE))
        top = max(0, int(self.canvas.canvasy(0) // CELL_SIZE))
        right = min(
            self.max_x - self.min_x + 1,
            int((self.canvas.canvasx(self.canvas.winfo_width()) // CELL_SIZE) + 1),
        )
        bottom = min(
            self.max_y - self.min_y + 1,
            int((self.canvas.canvasy(self.canvas.winfo_height()) // CELL_SIZE) + 1),
        )
        return left, top, max(left, right), max(top, bottom)

    def _draw_grid(self):
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return
        self.canvas.delete("all")
        left, top, right, bottom = self._visible_coordinates()
        for column in range(left, right):
            x = self.min_x + column
            for row in range(top, bottom):
                y = self.min_y + row
                x1 = column * CELL_SIZE
                y1 = row * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                arrow = self._get_arrow(x, y)
                if arrow is None or arrow.type == ArrowType.Empty:
                    fill = "#ffffff"
                    label = ""
                    direction = ""
                else:
                    try:
                        fill = _COLOR_HEX.get(Color(arrow.color), "#e8edf5")
                    except ValueError:
                        fill = "#e8edf5"
                    label = _short_type(arrow.type)
                    direction = _DIRECTION_GLYPHS[int(arrow.direction)]
                is_selected = self.last_position == (x, y)
                self.canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=fill,
                    outline="#c7cbd1",
                    width=1,
                )
                if label:
                    self.canvas.create_text(
                        x1 + CELL_SIZE // 2,
                        y1 + 16,
                        text=label,
                        fill="#20242a",
                        font=("TkDefaultFont", 9, "bold"),
                    )
                    self.canvas.create_text(
                        x1 + CELL_SIZE // 2,
                        y1 + 33,
                        text=direction,
                        fill="#414852",
                        font=("TkDefaultFont", 10),
                    )
                if is_selected:
                    self.canvas.create_rectangle(
                        x1 + 2,
                        y1 + 2,
                        x2 - 2,
                        y2 - 2,
                        outline="#1769aa",
                        width=2,
                    )
        self._draw_selection()

    def _draw_selection(self):
        if self.selection is None:
            return
        x1, y1, x2, y2 = self.selection
        self.canvas.create_rectangle(
            (x1 - self.min_x) * CELL_SIZE,
            (y1 - self.min_y) * CELL_SIZE,
            (x2 - self.min_x + 1) * CELL_SIZE,
            (y2 - self.min_y + 1) * CELL_SIZE,
            outline="#1769aa",
            fill="#1769aa",
            stipple="gray25",
            width=2,
        )

    def _get_arrow(self, x, y):
        chunk = self.map.chunks.get((x // 16, y // 16))
        return chunk.get(x % 16, y % 16) if chunk else None

    def _in_bounds(self, x, y):
        return self.min_x <= x <= self.max_x and self.min_y <= y <= self.max_y

    def _cell_at(self, event):
        column = int(self.canvas.canvasx(event.x) // CELL_SIZE)
        row = int(self.canvas.canvasy(event.y) // CELL_SIZE)
        if not (
            0 <= column <= self.max_x - self.min_x
            and 0 <= row <= self.max_y - self.min_y
        ):
            return None
        return self.min_x + column, self.min_y + row

    def _make_brush(self) -> Arrow:
        arrow = Arrow(
            type=ArrowType[self.type_var.get()],
            direction=Direction[self.direction_var.get()],
            flipped=self.flipped_var.get(),
        )
        arrow.color = Color[self.color_var.get()]
        arrow.bright = self.bright_var.get()
        arrow.letter = Letter[self.letter_var.get()]
        arrow.string = self.string_var.get()
        return arrow

    def _on_press(self, event):
        self.canvas.focus_set()
        position = self._cell_at(event)
        if position is None:
            return
        if self.select_mode:
            self.select_anchor = position
            self._set_selection(position, position)
        else:
            self._paint_cell(event)

    def _on_drag(self, event):
        if self.select_mode:
            position = self._cell_at(event)
            if position is not None and self.select_anchor is not None:
                self._set_selection(self.select_anchor, position)
        else:
            self._paint_cell(event)

    def _set_selection(self, a, b):
        self.selection = (
            min(a[0], b[0]),
            min(a[1], b[1]),
            max(a[0], b[0]),
            max(a[1], b[1]),
        )
        width = self.selection[2] - self.selection[0] + 1
        height = self.selection[3] - self.selection[1] + 1
        self.status_var.set(f"Выделено: {width}×{height}")
        self._draw_grid()

    def _paint_cell(self, event):
        position = self._cell_at(event)
        if position is None:
            return
        self.map.set(*position, self._make_brush())
        self.last_position = position
        self.status_var.set(f"Клетка ({position[0]}, {position[1]}) изменена.")
        self._draw_grid()

    def _sample_cell(self, event):
        position = self._cell_at(event)
        if position is None:
            return
        x, y = position
        arrow = self._get_arrow(x, y) or Arrow()
        self.type_var.set(arrow.type.name)
        self.direction_var.set(arrow.direction.name)
        self.flipped_var.set(arrow.flipped)
        try:
            self.color_var.set(Color(arrow.color).name)
        except ValueError:
            self.color_var.set(Color.White.name)
        self.bright_var.set(arrow.bright)
        try:
            self.letter_var.set(Letter(arrow.letter).name)
        except ValueError:
            self.letter_var.set(Letter.Empty.name)
        self.string_var.set(arrow.string)
        self.last_position = position
        self.status_var.set(f"Выбран образец из клетки ({x}, {y}).")
        self._draw_grid()

    def _show_coordinates(self, event):
        position = self._cell_at(event)
        self.hover_position = position
        if position is not None and not self.select_mode:
            self.status_var.set(f"Координаты: ({position[0]}, {position[1]})")

    def _mouse_wheel(self, event):
        direction = -1 if event.delta > 0 else 1
        if event.state & 0x0001:
            self._scroll_x("scroll", direction, "units")
        else:
            self._scroll_y("scroll", direction, "units")

    def _on_key(self, event):
        if isinstance(self.focus_get(), (tk.Entry, ttk.Entry)):
            return None
        if event.state & 0x0004 or event.state & 0x20000:
            return None
        action = _KEY_ACTIONS.get(event.keysym.lower())
        if action is None:
            return None
        if action in _DIRECTION_INDEX:
            self._set_direction(_DIRECTION_INDEX[action])
        elif action == "select":
            self._toggle_select_mode()
        elif action == "copy":
            self._copy()
        elif action == "paste":
            self._paste()
        elif action == "cut":
            self._copy()
            self._delete()
        elif action == "delete":
            self._delete()
        elif action == "cancel":
            self._cancel()
        return "break"

    def _set_direction(self, index):
        direction = Direction(index)
        self.direction_var.set(direction.name)
        if self.selection is None:
            self.status_var.set(f"Направление: {_DIRECTION_GLYPHS[index]}")
            return
        x1, y1, x2, y2 = self.selection
        changed = 0
        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                arrow = self._get_arrow(x, y)
                if arrow is None or arrow.type == ArrowType.Empty:
                    continue
                arrow = copy.deepcopy(arrow)
                arrow.direction = direction
                self.map.set(x, y, arrow)
                changed += 1
        self.status_var.set(f"Направление {_DIRECTION_GLYPHS[index]}: изменено стрелок — {changed}.")
        self._draw_grid()

    def _toggle_select_mode(self):
        self.select_mode = not self.select_mode
        self.canvas.configure(cursor="crosshair" if self.select_mode else "")
        if self.select_mode:
            self.status_var.set("Режим выделения: тяните мышью. E — выйти, Esc — снять выделение.")
        else:
            self.status_var.set("Режим рисования.")

    def _cancel(self):
        self.selection = None
        self.select_anchor = None
        if self.select_mode:
            self._toggle_select_mode()
        self.status_var.set("Выделение снято.")
        self._draw_grid()

    def _target_region(self):
        """Выделенная область, иначе клетка под курсором."""
        if self.selection is not None:
            return self.selection
        if self.hover_position is not None:
            x, y = self.hover_position
            return (x, y, x, y)
        return None

    def _copy(self):
        region = self._target_region()
        if region is None:
            return
        x1, y1, x2, y2 = region
        cells = []
        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                arrow = self._get_arrow(x, y)
                if arrow is not None and arrow.type != ArrowType.Empty:
                    cells.append((x - x1, y - y1, copy.deepcopy(arrow)))
        self.clipboard = (x2 - x1 + 1, y2 - y1 + 1, cells)
        self.status_var.set(f"Скопировано стрелок: {len(cells)}.")

    def _paste(self):
        if self.clipboard is None:
            self.status_var.set("Буфер пуст.")
            return
        if self.hover_position is None:
            self.status_var.set("Наведите курсор на карту, куда вставить.")
            return
        width, height, cells = self.clipboard
        ox, oy = self.hover_position
        for dx, dy, arrow in cells:
            x, y = ox + dx, oy + dy
            if self._in_bounds(x, y):
                self.map.set(x, y, copy.deepcopy(arrow))
        self.selection = (ox, oy, ox + width - 1, oy + height - 1)
        self.status_var.set(f"Вставлено стрелок: {len(cells)}.")
        self._draw_grid()

    def _delete(self):
        region = self._target_region()
        if region is None:
            return
        x1, y1, x2, y2 = region
        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                arrow = self._get_arrow(x, y)
                if arrow is not None and arrow.type != ArrowType.Empty:
                    self.map.set(x, y, Arrow())
        self.status_var.set("Удалено.")
        self._draw_grid()

    def _change_version(self, _event=None):
        self.map.version = int(self.version_var.get())
        self.canvas.focus_set()

    def _fit_map(self):
        positions = []
        for (chunk_x, chunk_y), chunk in self.map.chunks.items():
            for index, arrow in enumerate(chunk.arrows):
                if arrow.type != ArrowType.Empty:
                    positions.append(
                        (chunk_x * 16 + index % 16, chunk_y * 16 + index // 16)
                    )
        if not positions:
            self.min_x = INITIAL_MIN
            self.max_x = INITIAL_MAX
            self.min_y = INITIAL_MIN
            self.max_y = INITIAL_MAX
            return
        margin = 16
        self.min_x = min(INITIAL_MIN, min(x for x, _ in positions) - margin)
        self.max_x = max(INITIAL_MAX, max(x for x, _ in positions) + margin)
        self.min_y = min(INITIAL_MIN, min(y for _, y in positions) - margin)
        self.max_y = max(INITIAL_MAX, max(y for _, y in positions) + margin)

    def import_map(self):
        encoded = self.encoded_var.get().strip()
        if not encoded:
            messagebox.showerror("Импорт карты", "Введите строку карты.", parent=self)
            return
        try:
            imported = Map(encoded)
        except (
            AssertionError,
            binascii.Error,
            UnicodeError,
            ValueError,
            zlib.error,
        ) as error:
            messagebox.showerror(
                "Не удалось импортировать карту", str(error), parent=self
            )
            return
        self.map = imported
        self.version_var.set(str(imported.version))
        self.last_position = None
        self.selection = None
        self._fit_map()
        self._center_view()
        self.status_var.set("Карта импортирована.")

    def export_map(self):
        self.encoded_var.set("")
        try:
            self.encoded_var.set(self.map.export())
        except (ValueError, OverflowError) as error:
            messagebox.showerror(
                "Не удалось экспортировать карту", str(error), parent=self
            )
            return False
        self.status_var.set("Карта экспортирована в строку.")
        return True

    def copy_export(self):
        if not self.export_map():
            return
        self.clipboard_clear()
        self.clipboard_append(self.encoded_var.get())
        self.status_var.set("Строка карты скопирована в буфер обмена.")

    def open_file(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Открыть карту",
            filetypes=(("Текстовые файлы", "*.txt"), ("Все файлы", "*")),
        )
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as file:
                encoded = file.read().strip()
        except OSError as error:
            messagebox.showerror("Не удалось открыть файл", str(error), parent=self)
            return
        self.encoded_var.set(encoded)
        self.import_map()

    def save_file(self):
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Сохранить карту",
            defaultextension=".txt",
            filetypes=(("Текстовые файлы", "*.txt"), ("Все файлы", "*")),
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as file:
                file.write(self.map.export())
        except (OSError, ValueError, OverflowError) as error:
            messagebox.showerror(
                "Не удалось сохранить карту", str(error), parent=self
            )
            return
        self.status_var.set(f"Карта сохранена: {path}")


def main():
    ArrowEditor().mainloop()


if __name__ == "__main__":
    main()