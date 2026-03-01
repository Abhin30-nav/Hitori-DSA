class GridGraph:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.adj = {}
        self._build()

    def _build(self):
        for r in range(self.rows):
            for c in range(self.cols):
                self.adj[(r, c)] = self._neighbors(r, c)

    def _neighbors(self, r, c):
        nbrs = []
        for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                nbrs.append((nr, nc))
        return nbrs

    # public API used by BoardGame
    def neighbors(self, r, c):
        return self.adj.get((r, c), [])
