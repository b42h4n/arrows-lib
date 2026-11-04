import arrows

m = arrows.Map()

data = [
    [0, 1, 1, 0],
    [0, 1, 1, 1],
]

y = 0
for num in data:
    x = 0
    for bit in num:
        if bit == 0:
            m.get(x, y).type = arrows.ArrowType.Arrow
        else:
            m.get(x, y).type = arrows.ArrowType.SplitterUpRight
        m.get(x, y).direction = arrows.Direction.East
        m.get(x, y+1).type = arrows.ArrowType.BlueArrow
        m.get(x, y+1).direction = arrows.Direction.South
        x += 1
    m.get(-1, y).type = arrows.ArrowType.DirectionalButton
    m.get(-1, y).direction = arrows.Direction.East
    y += 2

print(m.export())
