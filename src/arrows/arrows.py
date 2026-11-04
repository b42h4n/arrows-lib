from enum import IntEnum
import base64
from typing import Self
import zlib

class Direction(IntEnum):
    North = 0
    East  = 1
    South = 2
    West  = 3

class ArrowType(IntEnum):
    Empty                  = 0
    Arrow                  = 1
    Source                 = 2
    Blocker                = 3
    Delay                  = 4
    Detector               = 5
    SplitterUpDown         = 6
    SplitterUpRight        = 7
    SplitterUpRightLeft    = 8
    Pulse                  = 9
    BlueArrow              = 10
    Diagonal               = 11
    BlueSplitterUpUp       = 12
    BlueSplitterRightUp    = 13
    BlueSplitterUpDiagonal = 14
    Not                    = 15
    And                    = 16
    Xor                    = 17
    Latch                  = 18
    Flipflop               = 19
    Random                 = 20
    Button                 = 21
    KeyboardButton         = 21
    LevelSource            = 22
    LevelTarget            = 23
    DirectionalButton      = 24
    Wall                   = 25
    Question               = 26
    Display                = 27
    DirectionalDisplay     = 28
    Note                   = 29
    Sender                 = 30
    SenderSignal           = 31
    TODO1                  = 32
    CommandBlock           = 33
    Logger                 = 34
    X                      = 35
    TODO2                  = 36
    TODO3                  = 37
    TODO4                  = 38
    TODO5                  = 39
    TODO6                  = 40
    TODO7                  = 41
    TODO8                  = 42
    TODO9                  = 43
    TODO10                 = 44
    TODO11                 = 45
    TODO12                 = 46
    TODO13                 = 47
    TODO14                 = 48
    TODO15                 = 49
    TODO16                 = 50
    TODO17                 = 51
    TODO18                 = 52
    TODO19                 = 53
    TODO20                 = 54
    TODO21                 = 55
    TODO22                 = 56
    TODO23                 = 57
    TODO24                 = 58
    TODO25                 = 59
    TODO26                 = 60
    TODO27                 = 61
    TODO28                 = 62
    TODO29                 = 63

class Color(IntEnum):
    White  = 0
    Red    = 1
    Blue   = 2
    Yellow = 3
    Green  = 4
    Orange = 5
    Purple = 6
    Black  = 7

class Instrument(IntEnum):
    Piano = 0
    Organ = 1
    SquareWave = 2
    TriangleWave = 3
    SawWave = 4
    Guitar = 5
    Harp = 6
    Violin = 7
    Cello = 8
    Contrabass = 9
    Bass = 10
    Flute = 11
    Oboe = 12
    Clarinet = 13
    Bassoon = 14
    Trumpet = 15
    Horn = 16
    Trombone = 17
    Tuba = 18
    Xylophone = 19
    Timpani = 20
    Drums = 21

class Note(IntEnum):
    C      = 0
    CSharp = 1
    D      = 2
    DSharp = 3
    E      = 4
    F      = 5
    FSharp = 6
    G      = 7
    GSharp = 8
    A      = 9
    ASharp = 10
    B      = 11

class Letter(IntEnum):
    Empty = 0
    A     = 1
    B     = 2
    C     = 3
    D     = 4
    E     = 5
    F     = 6
    G     = 7
    H     = 8
    I     = 9
    J     = 10
    K     = 11
    L     = 12
    M     = 13
    N     = 14
    O     = 15
    P     = 16
    Q     = 17
    R     = 18
    S     = 19
    T     = 20
    U     = 21
    V     = 22
    W     = 23
    X     = 24
    Y     = 25
    Z     = 26
    Zero  = 27
    One   = 28
    Two   = 29
    Three = 30
    Four  = 31
    Five  = 32
    Six   = 33
    Seven = 34
    Eight = 35
    Nine  = 36
    F1    = 37
    F2    = 38
    F3    = 39
    F4    = 40
    F5    = 41
    F6    = 42
    F7    = 43
    F8    = 44
    F9    = 45
    F10   = 46
    F11   = 47
    F12   = 48
    Space = 49
    Enter = 50
    Tab   = 51
    Shift = 52
    Ctrl  = 53
    Alt   = 54
    Back  = 55
    Up    = 56
    Down  = 57
    Left  = 58
    Right = 59

class Arrow:
    def __init__(self, type: ArrowType = ArrowType.Empty, direction: Direction = Direction.North, flipped = False):
        self.type = type
        self.direction = direction
        self.flipped = flipped
        self.string = ""
        self.letter = Letter(0)
        self.color = Color(0)
        self.bright = False
        self.instrument = Instrument(0)
        self.octave = 0
        self.note = Note(0)
        self.letter = Letter(0)

    direction: Direction = Direction.North
    flipped: bool = False
    type: ArrowType = ArrowType.Empty
    string: str

    # walls and bulbs
    color: Color
    bright: bool

    # music
    instrument: Instrument
    octave: int
    note: Note

    # walls and keyboard buttons
    letter: Letter

class Chunk:
    arrows: list[Arrow]

    def __init__(self):
        self.arrows = []
        for _ in range(256):
            self.arrows.append(Arrow())

    def get(self, x: int, y: int) -> Arrow:
        return self.arrows[y*16+x]

    def set(self, x: int, y: int, arrow: Arrow):
        self.arrows[y*16+x] = arrow

class Map:
    version: int
    chunks: dict[tuple[int, int], Chunk]

    def __init__(self, string: None|str = None):
        self.chunks = {}
        self.version = 0
        if string is not None:
            self.import_(string)

    def get(self, x: int, y: int) -> Arrow:
        chunk_x = x//16
        chunk_y = y//16
        arrow_x = x % 16
        arrow_y = y % 16
        if (chunk_x, chunk_y) not in self.chunks:
            self.chunks[(chunk_x, chunk_y)] = Chunk()
        return self.chunks[(chunk_x, chunk_y)].get(arrow_x, arrow_y)

    def set(self, x: int, y: int, arrow: Arrow):
        chunk_x = x//16
        chunk_y = y//16
        arrow_x = x % 16
        arrow_y = y % 16
        if (chunk_x, chunk_y) not in self.chunks:
            self.chunks[(chunk_x, chunk_y)] = Chunk()

        self.chunks[(chunk_x, chunk_y)].set(arrow_x, arrow_y, arrow)

    def import_(self, string: str):
        raw_data = base64.b64decode(string)
        def pop8() -> int:
            nonlocal raw_data
            val = raw_data[:1]
            raw_data = raw_data[1:]
            return int.from_bytes(val, byteorder='little')
        def pop16() -> int:
            nonlocal raw_data
            val = raw_data[:2]
            raw_data = raw_data[2:]
            return int.from_bytes(val, byteorder='little')

        self.version = pop16()
        assert self.version in {0, 4, 5}
        if self.version >= 4:
            compressed = pop8()
            if compressed:
                raw_data = zlib.decompress(raw_data)
        chunks_count = pop16()
        for _ in range(chunks_count):
            chunk_x = pop16()
            if chunk_x & 0x8000:
                chunk_x &= 0x7FFF
                chunk_x *= -1
            chunk_y = pop16()
            if chunk_y & 0x8000:
                chunk_y &= 0x7FFF
                chunk_y *= -1
            arrow_types = pop8()+1
            for _ in range(arrow_types):
                type = pop8()
                if type == ArrowType.Empty:
                    continue
                type_count = pop8()+1
                for _ in range(type_count):
                    arrow = Arrow()
                    arrow.type = ArrowType(type)
                    position = pop8()
                    x = position & 0x0F
                    y = (position & 0xF0) >> 4
                    dnf = pop8()
                    has_data = False
                    is_string = dnf & 0x10 != 0
                    if self.version == 4:
                        has_data = dnf & 1 != 0
                        dnf >>= 1
                    elif self.version == 5:
                        has_data = dnf & 0b1000
                    if has_data:
                        val = pop16()
                        if is_string:
                            strbuf = bytearray()
                            for _ in range(val):
                                strbuf.append(pop8())
                            arrow.string = strbuf.decode('utf-8')
                        else:
                            if arrow.type == ArrowType.Wall:
                                arrow.letter = (val >> 4) & 0x3F
                            if arrow.type == ArrowType.KeyboardButton:
                                arrow.letter = val
                            if arrow.type in {ArrowType.Wall, ArrowType.Display, ArrowType.DirectionalDisplay}:
                                arrow.color = val & 0x0F
                            if arrow.type == ArrowType.Display:
                                arrow.bright = val & 0x10
                    flipped = dnf & 0b0100 != 0
                    direction = dnf & 0b0011
                    arrow.flipped = flipped
                    arrow.direction = Direction(direction)
                    self.set(chunk_x*16 + x, chunk_y*16 + y, arrow)

    def export(self) -> str:
        raw_data = bytearray([])
        def push8(val: int):
            nonlocal raw_data
            raw_data.extend(val.to_bytes(byteorder='little', length=1))
        def push16(val: int):
            nonlocal raw_data
            raw_data.extend(val.to_bytes(byteorder='little', length=2))

        push16(len(self.chunks))
        for (chunk_x, chunk_y), chunk in self.chunks.items():
            types: list[ArrowType] = []
            for arrow in chunk.arrows:
                if arrow.type != ArrowType.Empty and arrow.type not in types:
                    types.append(arrow.type)
            if types == []: continue
            if chunk_x < 0:
                chunk_x *= -1
                chunk_x |= 0x8000
            if chunk_y < 0:
                chunk_y *= -1
                chunk_y |= 0x8000
            push16(chunk_x)
            push16(chunk_y)
            push8(len(types)-1)
            for type in types:
                push8(type)
                push8(0)
                types_count_index = len(raw_data)-1
                types_count = 0
                for x in range(16):
                    for y in range(16):
                        arrow = chunk.get(x, y)
                        if arrow.type != type: continue
                        position = x | (y << 4)
                        rotation = (arrow.direction | (arrow.flipped << 2)) << (1 if self.version == 4 else 0)
                        push8(position)
                        rotation_idx = len(raw_data)
                        push8(rotation)
                        has_data = False
                        if arrow.string:
                            has_data = True
                            raw_data[-1] |= 0x10
                            string_data = arrow.string.encode('utf-8')
                            push16(len(string_data))
                            for c in string_data:
                                push8(c)
                        else:
                            val = 0
                            if arrow.type  == ArrowType.Wall:
                                val |= arrow.letter << 4
                            if arrow.type == ArrowType.KeyboardButton:
                                val |= arrow.letter
                            if arrow.type in {ArrowType.Wall, ArrowType.Display, ArrowType.DirectionalDisplay}:
                                val |= arrow.color
                            if arrow.type == ArrowType.Display:
                                val |= arrow.bright << 4
                            if val != 0:
                                push16(val)
                                has_data = True
                        if has_data:
                            if self.version < 4:
                                raise ValueError("Embedding data(color, letter, string) into an arrow is only possible after v4")
                            raw_data[rotation_idx] |= 0x1 if self.version == 4 else 0x8
                        types_count += 1
                raw_data[types_count_index] = types_count-1
        if self.version >= 4:
            compressed = zlib.compress(raw_data, 9)
            is_compressed = False
            if len(compressed) < len(raw_data):
                raw_data = compressed
                is_compressed = True
            raw_data = (b'\1' if is_compressed else b'\0') + raw_data
        raw_data = self.version.to_bytes(byteorder='little', length=2) + raw_data
        return base64.b64encode(raw_data).decode('utf-8')

    def paste(self, x: int, y: int, src: Self|str):
        # for typecheck
        if isinstance(src, str):
            m = Map(src)
        else:
            m = src

        for chunk_x, chunk_y in m.chunks:
            chunk = m.chunks[(chunk_x, chunk_y)]
            for i, arrow in enumerate(chunk.arrows):
                arrow_x = chunk_x * 16 + i % 16 + x
                arrow_y = chunk_y * 16 + i // 16 + y
                self.set(arrow_x, arrow_y, arrow)
