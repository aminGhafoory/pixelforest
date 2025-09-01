import random
import csv
from collections import deque
from PIL import Image
from typing import Dict, Tuple, List

# ---- CONFIG ----
SIZE = 5           # board size (5x5) for generation
TILE_W = 12        # tileset tile width in pixels
TILE_H = 12        # tileset tile height in pixels
MARGIN = 1         # outer padding around the tileset (pixels)
SPACING = 1        # spacing between tiles in the tileset (pixels)

# Cell types
ROAD = "R"
OBSTACLE = "O"
DIRT = "D"

# Each cell type can have multiple possible tiles to pick from
DEFAULT_TILE_MAP: Dict[str, List[Tuple[int, int]]] = {
    OBSTACLE: [(0, 34), (1, 34), (2, 34), (3, 34), (17, 34)],
    ROAD: [(0, 5)],
    DIRT: [(0, 5)],
}

# --------- PATHFINDING / GENERATION ---------


def is_valid(sz: int, x: int, y: int) -> bool:
    return 0 <= x < sz and 0 <= y < sz


def bfs(board: List[List[str]], start_cells: List[Tuple[int, int]], target_check) -> bool:
    """Check if a path exists using BFS across non-obstacle cells."""
    sz = len(board)
    visited = [[False]*sz for _ in range(sz)]
    q = deque(start_cells)
    for x, y in start_cells:
        visited[x][y] = True
    while q:
        x, y = q.popleft()
        if target_check(x, y):
            return True
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = x+dx, y+dy
            if is_valid(sz, nx, ny) and not visited[nx][ny] and board[nx][ny] != OBSTACLE:
                visited[nx][ny] = True
                q.append((nx, ny))
    return False


def generate_board(num_obstacles: int) -> List[List[str]]:
    while True:
        # Initialize board with dirt
        board = [[DIRT for _ in range(SIZE)] for _ in range(SIZE)]

        # Place obstacles randomly
        cells = [(i, j) for i in range(SIZE) for j in range(SIZE)]
        random.shuffle(cells)
        for (x, y) in cells[:num_obstacles]:
            board[x][y] = OBSTACLE

        # Randomly mark some roads
        for (x, y) in cells[num_obstacles:]:
            if random.random() < 0.2:  # ~20% chance to become a road
                board[x][y] = ROAD

        # Ensure path from left → right
        left_cells = [(i, 0) for i in range(SIZE) if board[i][0] != OBSTACLE]
        def right_check(x, y): return y == SIZE-1
        if not bfs(board, left_cells, right_check):
            continue

        # Ensure path from top → bottom
        top_cells = [(0, j) for j in range(SIZE) if board[0][j] != OBSTACLE]
        def bottom_check(x, y): return x == SIZE-1
        if not bfs(board, top_cells, bottom_check):
            continue

        return board

# --------- I/O HELPERS ---------


def save_to_csv(board: List[List[str]], filename: str = "board.csv") -> None:
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(board)


def load_board_from_csv(csv_file: str) -> List[List[str]]:
    with open(csv_file, "r") as f:
        reader = csv.reader(f)
        board = []
        for row in reader:
            clean = [cell.strip() for cell in row if cell.strip()]
            if clean:
                board.append(clean)
    if not board:
        raise ValueError("CSV appears empty.")
    w = len(board[0])
    if any(len(r) != w for r in board):
        raise ValueError(
            "CSV rows have inconsistent lengths; ensure a rectangular grid.")
    return board

# --------- IMAGE RENDERING ---------


def _tile_box(tx: int, ty: int, tile_w: int, tile_h: int, margin: int, spacing: int) -> Tuple[int, int, int, int]:
    x = margin + tx * (tile_w + spacing)
    y = margin + ty * (tile_h + spacing)
    return (x, y, x + tile_w, y + tile_h)


def csv_to_image(
    csv_file: str,
    tileset_file: str,
    output_file: str,
    tile_map: Dict[str, List[Tuple[int, int]]] = None,
    tile_w: int = TILE_W,
    tile_h: int = TILE_H,
    margin: int = MARGIN,
    spacing: int = SPACING,
) -> None:
    board = load_board_from_csv(csv_file)
    rows, cols = len(board), len(board[0])

    tileset = Image.open(tileset_file).convert("RGBA")
    tile_map = tile_map or DEFAULT_TILE_MAP

    # Create final image in RGB mode with white background
    img = Image.new("RGB", (cols * tile_w, rows * tile_h), (255, 255, 255))

    for i in range(rows):
        for j in range(cols):
            cell = board[i][j]
            if cell not in tile_map:
                raise KeyError(
                    f"No tile mapping for cell '{cell}'. Update tile_map.")
            tx, ty = random.choice(tile_map[cell])
            box = _tile_box(tx, ty, tile_w, tile_h, margin, spacing)
            tile = tileset.crop(box)
            tile = tile.convert("RGBA")
            datas = tile.getdata()
            new_data = []
            for item in datas:
                # if pixel is black (0,0,0), make it white
                if item[:3] == (0, 0, 0):
                    new_data.append((255, 255, 255, item[3]))
                else:
                    new_data.append(item)
            tile.putdata(new_data)

            # Composite tile over white background
            tile_rgb = Image.new("RGB", (tile_w, tile_h), (255, 255, 255))
            tile_rgb.paste(tile, (0, 0), tile)  # use alpha channel

            img.paste(tile_rgb, (j * tile_w, i * tile_h))

    scale_factor = 10
    img_resized = img.resize(
        (img.width * scale_factor, img.height * scale_factor), resample=Image.NEAREST)
    img_resized = img_resized.convert("L")  # "L" = 8-bit grayscale
    img_resized.save(output_file)
    print(f"Saved image: {output_file}")


# --------- DEMO / MAIN ---------
if __name__ == "__main__":
    num_obstacles = 15  # adjustable number of obstacles
    for i in range(50):
        board = generate_board(num_obstacles)
        for row in board:
            print(" ".join(row))
        save_to_csv(board, f"boards/board{i}.csv")
        print(f"Board saved to board{i}.csv")

        csv_to_image(
            csv_file=f"boards/board{i}.csv",
            tileset_file="urizen_onebit_tileset__v2d0.png",
            output_file=f"output/board{i}.png",
            tile_map=DEFAULT_TILE_MAP,
            tile_w=TILE_W,
            tile_h=TILE_H,
            margin=MARGIN,
            spacing=SPACING,
        )
