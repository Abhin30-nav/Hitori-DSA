from BoardGame import BoardGame

class Hitori:
    def __init__(self):
        # Harder 5x5 puzzle:
        # - Each row has exactly one duplicate (first/last cell)
        # - Minimal solution requires 5 black cells
        # - Solvable by current greedy AI
        grid = [
            [1, 2, 3, 4, 1],
            [2, 3, 4, 5, 2],
            [3, 4, 5, 1, 3],
            [4, 5, 1, 2, 4],
            [5, 1, 2, 3, 5],
        ]

        self.board_game = BoardGame(grid)

    def board(self):
        return self.board_game
