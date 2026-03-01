from Constants import CELL_WHITE, CELL_BLACK
from collections import deque
from GridGraph import GridGraph


class BoardGame:
    def __init__(self, grid):
        self.grid = grid
        self.rows_n = len(grid)
        self.cols_n = len(grid[0])
        self.state = [
            [CELL_WHITE for _ in range(self.cols_n)]
            for _ in range(self.rows_n)
        ]

        # shared graph for adjacency/connectedness
        self.graph = GridGraph(self.rows_n, self.cols_n)

    def rows(self):
        return self.rows_n

    def cols(self):
        return self.cols_n

    def value_at(self, r, c):
        return self.grid[r][c]

    def cell_state(self, r, c):
        return self.state[r][c]

    def toggle_cell(self, r, c):
        if self.state[r][c] == CELL_WHITE:
            self.state[r][c] = CELL_BLACK
        else:
            self.state[r][c] = CELL_WHITE

    def set_state_from_grid(self, new_state):
        """Force the board to a specific state (used for simulation)."""
        self.state = [row[:] for row in new_state]

    def clone(self):
        """Create a deep copy of this game instance."""
        new_game = BoardGame(self.grid)
        new_game.state = [row[:] for row in self.state]
        return new_game

    # ---------- RULE CHECKS ----------

    def has_black_cells(self):
        for r in range(self.rows_n):
            for c in range(self.cols_n):
                if self.state[r][c] == CELL_BLACK:
                    return True
        return False

    def no_duplicates(self):
        # Rows
        for r in range(self.rows_n):
            seen = set()
            for c in range(self.cols_n):
                if self.state[r][c] == CELL_WHITE:
                    v = self.grid[r][c]
                    if v in seen:
                        return False
                    seen.add(v)

        # Columns
        for c in range(self.cols_n):
            seen = set()
            for r in range(self.rows_n):
                if self.state[r][c] == CELL_WHITE:
                    v = self.grid[r][c]
                    if v in seen:
                        return False
                    seen.add(v)

        return True

    def no_adjacent_black(self):
        for r in range(self.rows_n):
            for c in range(self.cols_n):
                if self.state[r][c] == CELL_BLACK:
                    for nr, nc in self.graph.neighbors(r, c):
                        if self.state[nr][nc] == CELL_BLACK:
                            return False
        return True

    def white_connected(self):
        visited = set()
        q = deque()

        for r in range(self.rows_n):
            for c in range(self.cols_n):
                if self.state[r][c] == CELL_WHITE:
                    q.append((r, c))
                    visited.add((r, c))
                    break
            if q:
                break

        if not q:
            return False

        while q:
            r, c = q.popleft()
            for nr, nc in self.graph.neighbors(r, c):
                if (
                    self.state[nr][nc] == CELL_WHITE and
                    (nr, nc) not in visited
                ):
                    visited.add((nr, nc))
                    q.append((nr, nc))

        for r in range(self.rows_n):
            for c in range(self.cols_n):
                if self.state[r][c] == CELL_WHITE and (r, c) not in visited:
                    return False

        return True

    def is_solved(self):
        """
        Completion rule (per request):
          1) no duplicates among white cells in any row/column, AND
          2) no adjacent black cells
        """
        return (
            self.no_duplicates() and
            self.no_adjacent_black()
        )

    def solve_issues(self):
        """
        Issue reporting aligned with is_solved():
        Only report duplicates/adjacent-black problems. Do not report connectivity.
        """
        issues = []
        if not self.no_duplicates():
            issues.append("remove duplicates in each row/column (among white cells)")
        if not self.no_adjacent_black():
            issues.append("no adjacent black cells")
        return issues

    # ---------- DIVIDE AND CONQUER SOLVER ----------

    def get_dc_solution_grid(self):
        """
        Runs the Divide and Conquer algorithm on a clone of the board
        and returns the final state 2D array.
        This allows the UI to 'animate' the moves towards this state.
        """
        sim_board = self.clone()
        sim_board.divide_and_conquer_solve()
        return sim_board.state

    def divide_and_conquer_solve(self):
        """
        1. Divides the board into recursive sub-grids.
        2. Solves sub-grids independently.
        3. Merges them and repairs boundary conflicts.
        """
        # 1. Run recursive D&C
        solution_grid = self._dc_recursive(self.grid)
        
        # 2. Apply merged state
        if solution_grid:
            self.state = solution_grid
        
        # 3. Final Repair: D&C might leave minor inconsistencies.
        # Run a quick greedy pass to clean up.
        if not self.is_solved():
            self.greedy_solver(max_steps=self.rows_n * self.cols_n)
            
        return self.is_solved()

    def _dc_recursive(self, grid_slice):
        rows = len(grid_slice)
        cols = len(grid_slice[0])

        # BASE CASE: Small enough (<= 25 cells) for Exact Solver
        if rows * cols <= 25:
            # Create a mini board for this slice
            sub_game = BoardGame(grid_slice)
            sol = sub_game.find_min_black_solution_state()
            return sol if sol else sub_game.state

        # RECURSIVE STEP
        if rows >= cols:
            # Split Horizontally (Top / Bottom)
            mid = rows // 2
            top_grid = grid_slice[:mid]
            bottom_grid = grid_slice[mid:]

            top_sol = self._dc_recursive(top_grid)
            bottom_sol = self._dc_recursive(bottom_grid)

            return self._merge_grids(top_sol, bottom_sol, axis="vertical", original_vals=grid_slice)
        else:
            # Split Vertically (Left / Right)
            mid = cols // 2
            left_grid = [r[:mid] for r in grid_slice]
            right_grid = [r[mid:] for r in grid_slice]

            left_sol = self._dc_recursive(left_grid)
            right_sol = self._dc_recursive(right_grid)

            return self._merge_grids(left_sol, right_sol, axis="horizontal", original_vals=grid_slice)

    def _merge_grids(self, part_a, part_b, axis, original_vals):
        """
        Merges two solved sub-states and repairs boundary conflicts.
        """
        merged_state = []
        if axis == "vertical":
            merged_state = part_a + part_b
        else:
            rows = len(part_a)
            for r in range(rows):
                merged_state.append(part_a[r] + part_b[r])

        # Repair Phase using a temp board
        temp_board = BoardGame(original_vals)
        temp_board.state = merged_state

        self._repair_boundary_adjacency(temp_board, axis, len(part_a), len(part_a[0]))
        self._repair_new_duplicates(temp_board, axis)

        return temp_board.state

    def _repair_boundary_adjacency(self, board, axis, split_idx_r, split_idx_c):
        rows = board.rows()
        cols = board.cols()

        if axis == "vertical":
            # Check seam: row (split_idx_r - 1) and row (split_idx_r)
            r_top = split_idx_r - 1
            r_btm = split_idx_r
            if 0 <= r_top < rows and 0 <= r_btm < rows:
                for c in range(cols):
                    if board.state[r_top][c] == CELL_BLACK and board.state[r_btm][c] == CELL_BLACK:
                        # Fix: Turn bottom one white
                        board.state[r_btm][c] = CELL_WHITE

        else: # horizontal
            # Check seam: col (split_idx_c - 1) and col (split_idx_c)
            c_left = split_idx_c - 1
            c_right = split_idx_c
            if 0 <= c_left < cols and 0 <= c_right < cols:
                for r in range(rows):
                    if board.state[r][c_left] == CELL_BLACK and board.state[r][c_right] == CELL_BLACK:
                        # Fix: Turn right one white
                        board.state[r][c_right] = CELL_WHITE

    def _repair_new_duplicates(self, board, axis):
        rows = board.rows()
        cols = board.cols()

        if axis == "vertical":
            # Top/Bottom merged -> Check Columns
            for c in range(cols):
                counts = {}
                for r in range(rows):
                    if board.state[r][c] == CELL_WHITE:
                        val = board.grid[r][c]
                        counts[val] = counts.get(val, []) + [(r, c)]
                
                for val, locations in counts.items():
                    if len(locations) > 1:
                        # Keep first, blacken rest if safe
                        for i in range(1, len(locations)):
                            rr, cc = locations[i]
                            board.state[rr][cc] = CELL_BLACK
                            if not board.no_adjacent_black():
                                board.state[rr][cc] = CELL_WHITE
        else:
            # Left/Right merged -> Check Rows
            for r in range(rows):
                counts = {}
                for c in range(cols):
                    if board.state[r][c] == CELL_WHITE:
                        val = board.grid[r][c]
                        counts[val] = counts.get(val, []) + [(r, c)]
                
                for val, locations in counts.items():
                    if len(locations) > 1:
                        for i in range(1, len(locations)):
                            rr, cc = locations[i]
                            board.state[rr][cc] = CELL_BLACK
                            if not board.no_adjacent_black():
                                board.state[rr][cc] = CELL_WHITE

    # ---------- GREEDY SOLVER ----------

    def duplicate_conflict_score(self):
        """Count "extra" duplicate occurrences among WHITE cells (rows + cols)."""
        score = 0

        for r in range(self.rows_n):
            counts = {}
            for c in range(self.cols_n):
                if self.state[r][c] == CELL_WHITE:
                    v = self.grid[r][c]
                    counts[v] = counts.get(v, 0) + 1
            for k in counts.values():
                if k > 1:
                    score += (k - 1)

        for c in range(self.cols_n):
            counts = {}
            for r in range(self.rows_n):
                if self.state[r][c] == CELL_WHITE:
                    v = self.grid[r][c]
                    counts[v] = counts.get(v, 0) + 1
            for k in counts.values():
                if k > 1:
                    score += (k - 1)

        return score

    def greedy_move(self):
        """Perform one greedy move.

        Greedily blackens a WHITE cell that participates in a duplicate (row/col)
        if it preserves core constraints (no adjacent blacks + white connected)
        and strictly reduces the duplicate-conflict score. No backtracking.

        Returns True if a move was applied, else False.
        """

        base = self.duplicate_conflict_score()
        if base == 0:
            return False

        # Precompute counts to identify duplicate-participating cells
        row_counts = []
        for r in range(self.rows_n):
            counts = {}
            for c in range(self.cols_n):
                if self.state[r][c] == CELL_WHITE:
                    v = self.grid[r][c]
                    counts[v] = counts.get(v, 0) + 1
            row_counts.append(counts)

        col_counts = []
        for c in range(self.cols_n):
            counts = {}
            for r in range(self.rows_n):
                if self.state[r][c] == CELL_WHITE:
                    v = self.grid[r][c]
                    counts[v] = counts.get(v, 0) + 1
            col_counts.append(counts)

        best = None  # (reduction, r, c)

        for r in range(self.rows_n):
            for c in range(self.cols_n):
                if self.state[r][c] != CELL_WHITE:
                    continue

                v = self.grid[r][c]
                in_dup = (row_counts[r].get(v, 0) > 1) or (col_counts[c].get(v, 0) > 1)
                if not in_dup:
                    continue

                self.state[r][c] = CELL_BLACK
                if self.no_adjacent_black() and self.white_connected():
                    after = self.duplicate_conflict_score()
                    reduction = base - after
                    if reduction > 0:
                        cand = (reduction, r, c)
                        if best is None or cand > best:
                            best = cand
                self.state[r][c] = CELL_WHITE

        if best is None:
            return False

        _, r, c = best
        self.state[r][c] = CELL_BLACK
        return True

    def greedy_solver(self, max_steps=None):
        """Keep applying greedy moves until solved or stuck."""
        if max_steps is None:
            max_steps = self.rows_n * self.cols_n * 10

        steps = 0
        while not self.is_solved() and steps < max_steps:
            if not self.greedy_move():
                break
            steps += 1

        return self.is_solved()

    # ---------- EXACT SOLVER (for Solution UI) ----------

    def find_solution_state(self):
        """Find a solved state minimizing the number of black cells.
        Returns a 2D list of CELL_WHITE/CELL_BLACK if a solution is found,
        otherwise returns None.
        """
        return self.find_min_black_solution_state()

    def find_min_black_solution_state(self):
        """Find an exact solved state with the minimum number of black cells."""
        rows_n, cols_n = self.rows_n, self.cols_n
        graph = self.graph  # reuse GridGraph here too

        # None = unassigned, CELL_WHITE, CELL_BLACK
        assign = [[None for _ in range(cols_n)] for _ in range(rows_n)]

        # Track how many whites chosen per (row,value) and (col,value)
        row_white_counts = [dict() for _ in range(rows_n)]
        col_white_counts = [dict() for _ in range(cols_n)]

        # Heuristic ordering: cells with higher duplicate pressure first
        row_freq = [dict() for _ in range(rows_n)]
        col_freq = [dict() for _ in range(cols_n)]
        for r in range(rows_n):
            for c in range(cols_n):
                v = self.grid[r][c]
                row_freq[r][v] = row_freq[r].get(v, 0) + 1
                col_freq[c][v] = col_freq[c].get(v, 0) + 1

        positions = [(r, c) for r in range(rows_n) for c in range(cols_n)]
        # 1. Pre-calculate the heuristic score for each cell
        scored_positions = []
        for r in range(rows_n):
            for c in range(cols_n):
                v = self.grid[r][c]
                score = row_freq[r][v] + col_freq[c][v]
                scored_positions.append((score, r, c))

        # 2. Define the custom Merge Sort (sorting in descending order)
        def merge_sort_desc(arr):
            # Base case: arrays of length 0 or 1 are already sorted
            if len(arr) <= 1:
                return arr
                
            # Divide
            mid = len(arr) // 2
            left = merge_sort_desc(arr[:mid])
            right = merge_sort_desc(arr[mid:])
            
            # Conquer & Combine (Merge)
            merged = []
            i = j = 0
            while i < len(left) and j < len(right):
                # Compare the score (index 0 of the tuple)
                if left[i][0] >= right[j][0]: 
                    merged.append(left[i])
                    i += 1
                else:
                    merged.append(right[j])
                    j += 1
                    
            # Append any remaining elements
            merged.extend(left[i:])
            merged.extend(right[j:])
            return merged

        # 3. Apply the sort and extract just the (r, c) positions back out
        sorted_scored_positions = merge_sort_desc(scored_positions)
        positions = [(r, c) for score, r, c in sorted_scored_positions]

        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        def any_adjacent_black(r, c):
            for nr, nc in graph.neighbors(r, c):
                if assign[nr][nc] == CELL_BLACK:
                    return True
            return False

        def connectivity_possible():
            # If there are no assigned whites yet, connectivity is still possible.
            start = None
            whites = []

            for r in range(rows_n):
                for c in range(cols_n):
                    if assign[r][c] == CELL_WHITE:
                        whites.append((r, c))
                        if start is None:
                            start = (r, c)

            if not whites:
                return True

            q = deque([start])
            seen = {start}
            while q:
                r, c = q.popleft()
                for nr, nc in graph.neighbors(r, c):
                    if (nr, nc) in seen:
                        continue
                    # Black cells are walls; unassigned cells are potentially white.
                    if assign[nr][nc] == CELL_BLACK:
                        continue
                    seen.add((nr, nc))
                    q.append((nr, nc))

            # All currently assigned whites must be reachable via non-black cells.
            for rc in whites:
                if rc not in seen:
                    return False
            return True

        def final_white_connected(sol_state):
            visited = set()
            q = deque()

            for r in range(rows_n):
                for c in range(cols_n):
                    if sol_state[r][c] == CELL_WHITE:
                        q.append((r, c))
                        visited.add((r, c))
                        break
                if q:
                    break

            if not q:
                return False

            while q:
                r, c = q.popleft()
                for nr, nc in graph.neighbors(r, c):
                    if sol_state[nr][nc] == CELL_WHITE and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        q.append((nr, nc))

            for r in range(rows_n):
                for c in range(cols_n):
                    if sol_state[r][c] == CELL_WHITE and (r, c) not in visited:
                        return False
            return True

        best_solution = None
        best_black = rows_n * cols_n + 1

        def build_solution_from_assign():
            sol = [[CELL_WHITE for _ in range(cols_n)] for _ in range(rows_n)]
            for rr in range(rows_n):
                for cc in range(cols_n):
                    if assign[rr][cc] is None:
                        return None
                    sol[rr][cc] = assign[rr][cc]
            return sol

        def backtrack(i, blacks):
            nonlocal best_solution, best_black

            if blacks >= best_black:
                return

            if i >= len(positions):
                sol = build_solution_from_assign()
                if sol is None:
                    return
                if not final_white_connected(sol):
                    return
                best_solution = sol
                best_black = blacks
                return

            r, c = positions[i]
            v = self.grid[r][c]

            # Try WHITE first
            if row_white_counts[r].get(v, 0) == 0 and col_white_counts[c].get(v, 0) == 0:
                assign[r][c] = CELL_WHITE
                row_white_counts[r][v] = row_white_counts[r].get(v, 0) + 1
                col_white_counts[c][v] = col_white_counts[c].get(v, 0) + 1

                if connectivity_possible():
                    backtrack(i + 1, blacks)

                row_white_counts[r][v] -= 1
                if row_white_counts[r][v] <= 0:
                    del row_white_counts[r][v]
                col_white_counts[c][v] -= 1
                if col_white_counts[c][v] <= 0:
                    del col_white_counts[c][v]
                assign[r][c] = None

            # Try BLACK
            if not any_adjacent_black(r, c):
                assign[r][c] = CELL_BLACK
                if connectivity_possible():
                    backtrack(i + 1, blacks + 1)
                assign[r][c] = None

        backtrack(0, 0)
        return best_solution