import asyncio
import time
import flet as ft
from Hitori import Hitori
from BoardGame import BoardGame
from Constants import CELL_BLACK, CELL_WHITE

CELL_SIZE = 60

MODE_MANUAL = "Manual"
MODE_COMPUTER = "Computer-only"
MODE_PVC = "Player with computer"

ALGO_GREEDY = "Greedy"
ALGO_DC = "Divide & Conquer"

def run_dc_with_timer(grid_snapshot):
    """
    Runs the Divide & Conquer solver in a separate thread and measures
    STRICT CPU process_time, excluding thread scheduling and asyncio overhead.
    """
    solver = BoardGame(grid_snapshot)
    
    t_start = time.process_time()
    result_state = solver.get_dc_solution_grid()
    t_end = time.process_time()
    
    return result_state, (t_end - t_start)

def main(page: ft.Page):
    # ---------------- PAGE SETUP ----------------
    page.title = "Hitori Game (Flet)"
    page.window_width = 460
    page.window_height = 800
    page.padding = 14

    # ---------------- GAME STATE ----------------
    game = Hitori()
    board = game.board()

    solved_shown = False
    input_locked = False

    ai_gen = 0
    pvc_gen = 0

    moves = 0
    player_correct = 0
    computer_correct = 0
    wrong_black_removed = 0

    current_mode = MODE_MANUAL
    current_algorithm = ALGO_GREEDY

    solution_dialog_gen = 0
    solution_cache_gen = 0
    solution_cache = None
    solution_cache_started = False

    # ---------------- ROOT ----------------
    snack = ft.SnackBar(content=ft.Text(""), bgcolor=ft.Colors.GREEN_700)
    page.snack_bar = snack
    root = ft.Container(expand=True)
    page.add(root)

    # ---------------- GAME UI CONTROLS ----------------
    grid_view = ft.Column(spacing=0)

    mode_label = ft.Text("", size=13, color=ft.Colors.GREY_700, weight=ft.FontWeight.W_600)
    status = ft.Text("", size=16, color=ft.Colors.GREEN_700, weight=ft.FontWeight.BOLD)
    moves_text = ft.Text("Moves: 0", size=14, color=ft.Colors.BLUE_700, weight=ft.FontWeight.BOLD)
    timer_text = ft.Text("CPU Time: 0.0000s", size=14, color=ft.Colors.PURPLE_700, weight=ft.FontWeight.BOLD)

    player_correct_text = ft.Text("Player correct: 0", size=16, color=ft.Colors.BLUE_900, weight=ft.FontWeight.BOLD)
    computer_correct_text = ft.Text("Computer correct: 0", size=16, color=ft.Colors.GREEN_900, weight=ft.FontWeight.BOLD)
    wrong_black_removed_text = ft.Text("Wrong black removed: 0", size=16, color=ft.Colors.RED_900, weight=ft.FontWeight.BOLD)

    player_counter_card = ft.Container(
        expand=1, padding=ft.padding.symmetric(horizontal=12, vertical=10),
        bgcolor=ft.Colors.BLUE_50, border=ft.border.all(1, ft.Colors.BLUE_200),
        border_radius=12, alignment=ft.alignment.center, content=player_correct_text,
    )
    computer_counter_card = ft.Container(
        expand=1, padding=ft.padding.symmetric(horizontal=12, vertical=10),
        bgcolor=ft.Colors.GREEN_50, border=ft.border.all(1, ft.Colors.GREEN_200),
        border_radius=12, alignment=ft.alignment.center, content=computer_correct_text,
    )
    wrong_removed_counter_card = ft.Container(
        expand=1, padding=ft.padding.symmetric(horizontal=12, vertical=10),
        bgcolor=ft.Colors.RED_50, border=ft.border.all(1, ft.Colors.RED_200),
        border_radius=12, alignment=ft.alignment.center, content=wrong_black_removed_text,
    )

    pvc_counters_row = ft.Container(
        visible=False,
        content=ft.Row(
            [player_counter_card, computer_counter_card, wrong_removed_counter_card],
            spacing=12, alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    completion_actions = ft.Row(spacing=10, visible=False)

    solution_btn = ft.OutlinedButton("Solution", icon=ft.Icons.LIGHTBULB_OUTLINE, visible=False)
    graph_btn = ft.OutlinedButton("Graph", icon=ft.Icons.DEVICE_HUB_OUTLINED, visible=False)

    solution_dialog = ft.AlertDialog(
        modal=True, title=ft.Text("Solution (black cells)"), content=ft.Text(""),
        actions=[ft.TextButton("Close")], actions_alignment=ft.MainAxisAlignment.END,
    )

    graph_dialog = ft.AlertDialog(
        modal=True, title=ft.Text("Grid graph (nodes & edges)"), content=ft.Text(""),
        actions=[ft.TextButton("Close")], actions_alignment=ft.MainAxisAlignment.END,
    )

    def open_dialog(dlg: ft.AlertDialog):
        try:
            page.open(dlg)
        except Exception:
            page.dialog = dlg
            dlg.open = True
            page.update()

    def close_dialog(dlg: ft.AlertDialog):
        try:
            page.close(dlg)
        except Exception:
            dlg.open = False
            page.update()

    solution_dialog.actions[0].on_click = lambda _: close_dialog(solution_dialog)
    graph_dialog.actions[0].on_click = lambda _: close_dialog(graph_dialog)

    def build_graph_view(rows: int, cols: int, values_grid):
        margin, spacing, radius, thickness = 22, 56, 14, 3
        width = margin * 2 + (cols - 1) * spacing + radius * 2
        height = margin * 2 + (rows - 1) * spacing + radius * 2
        shapes = []

        def node_center(rr: int, cc: int):
            return margin + cc * spacing, margin + rr * spacing

        for rr in range(rows):
            for cc in range(cols):
                cx, cy = node_center(rr, cc)
                if cc + 1 < cols:
                    shapes.append(ft.Container(left=cx, top=cy - thickness / 2, width=spacing, height=thickness, bgcolor=ft.Colors.GREY_400))
                if rr + 1 < rows:
                    shapes.append(ft.Container(left=cx - thickness / 2, top=cy, width=thickness, height=spacing, bgcolor=ft.Colors.GREY_400))

        for rr in range(rows):
            for cc in range(cols):
                cx, cy = node_center(rr, cc)
                shapes.append(ft.Container(
                    left=cx - radius, top=cy - radius, width=radius * 2, height=radius * 2,
                    bgcolor=ft.Colors.BLUE_700, border_radius=radius, border=ft.border.all(1, ft.Colors.BLUE_900),
                    alignment=ft.alignment.center,
                    content=ft.Text(str(values_grid[rr][cc]), size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                ))

        return ft.Container(width=width, height=height, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=10, padding=10, content=ft.Stack(controls=shapes, width=width, height=height))

    def build_solution_grid(sol_state):
        size = 24
        rows = []
        for r in range(len(sol_state)):
            row = ft.Row(spacing=2)
            for c in range(len(sol_state[0])):
                is_black = sol_state[r][c] == CELL_BLACK
                row.controls.append(ft.Container(width=size, height=size, bgcolor=ft.Colors.BLACK if is_black else ft.Colors.WHITE, border=ft.border.all(1, ft.Colors.GREY_400), border_radius=5))
            rows.append(row)
        return ft.Column(rows, spacing=2, tight=True)

    async def compute_solution_task(gen: int):
        nonlocal solution_cache
        try:
            solver = BoardGame(board.grid)
            loop = asyncio.get_running_loop()
            sol = await loop.run_in_executor(None, solver.find_solution_state)
        except Exception as ex:
            if gen != solution_dialog_gen:
                return
            solution_dialog.content = ft.Text(f"Error computing solution: {ex}")
            page.update()
            return

        if gen != solution_dialog_gen:
            return

        if sol is None:
            solution_dialog.content = ft.Text("Solution not found for this puzzle.")
            page.update()
            return

        solution_cache = sol
        black_count = sum(1 for rr in sol for cc in rr if cc == CELL_BLACK)
        solution_dialog.content = ft.Column(
            [ft.Text(f"Minimal solution (black cells: {black_count})", size=12, color=ft.Colors.GREY_700, weight=ft.FontWeight.BOLD),
             ft.Container(padding=ft.padding.only(top=8), content=build_solution_grid(sol))],
            spacing=8, tight=True,
        )
        page.update()

    async def compute_solution_cache_task(gen: int):
        nonlocal solution_cache
        try:
            solver = BoardGame(board.grid)
            loop = asyncio.get_running_loop()
            sol = await loop.run_in_executor(None, solver.find_solution_state)
            if gen == solution_cache_gen:
                solution_cache = sol
        except Exception:
            return

    def ensure_solution_cache_started():
        nonlocal solution_cache_gen, solution_cache_started
        if solution_cache is not None or solution_cache_started:
            return
        solution_cache_started = True
        solution_cache_gen += 1
        page.run_task(compute_solution_cache_task, solution_cache_gen)

    def count_black_cells():
        return sum(1 for rr in range(board.rows()) for cc in range(board.cols()) if board.cell_state(rr, cc) == CELL_BLACK)

    def pvc_correcting_move():
        if solution_cache is None:
            base_score = board.duplicate_conflict_score()
            if base_score == 0:
                return None
            best = None
            for r in range(board.rows()):
                for c in range(board.cols()):
                    if board.cell_state(r, c) != CELL_WHITE:
                        continue
                    board.toggle_cell(r, c)
                    if board.no_adjacent_black():
                        after = board.duplicate_conflict_score()
                        reduction = base_score - after
                        if reduction > 0:
                            cand = (reduction, r, c)
                            if best is None or cand > best:
                                best = cand
                    board.toggle_cell(r, c)
            if best is None:
                return None
            _, r, c = best
            board.toggle_cell(r, c)
            return "added"

        def can_add_any_correct_black() -> bool:
            for r in range(board.rows()):
                for c in range(board.cols()):
                    if solution_cache[r][c] != CELL_BLACK or board.cell_state(r, c) != CELL_WHITE:
                        continue
                    board.toggle_cell(r, c)
                    ok = board.no_adjacent_black()
                    board.toggle_cell(r, c)
                    if ok:
                        return True
            return False

        base_score = board.duplicate_conflict_score()
        best = None
        for r in range(board.rows()):
            for c in range(board.cols()):
                if solution_cache[r][c] != CELL_BLACK or board.cell_state(r, c) != CELL_WHITE:
                    continue
                board.toggle_cell(r, c)
                if board.no_adjacent_black():
                    after = board.duplicate_conflict_score()
                    reduction = base_score - after
                    cand = (reduction, r, c)
                    if best is None or cand > best:
                        best = cand
                board.toggle_cell(r, c)

        if best is not None:
            _, r, c = best
            board.toggle_cell(r, c)
            return "added"

        wrong_blacks = [(r, c) for r in range(board.rows()) for c in range(board.cols()) if board.cell_state(r, c) == CELL_BLACK and solution_cache[r][c] == CELL_WHITE]
        for r, c in wrong_blacks:
            board.toggle_cell(r, c)
            if can_add_any_correct_black():
                return "removed"
            board.toggle_cell(r, c)
        return None

    def show_solution(_=None):
        nonlocal solution_dialog_gen
        if current_mode != MODE_MANUAL:
            snack.content.value = "Solution is available only in Manual mode."
            snack.bgcolor = ft.Colors.RED_700
            snack.open = True
            page.update()
            return

        if solution_cache is not None:
            black_count = sum(1 for rr in solution_cache for cc in rr if cc == CELL_BLACK)
            solution_dialog.content = ft.Column([ft.Text(f"Minimal solution (black cells: {black_count})", size=12, color=ft.Colors.GREY_700, weight=ft.FontWeight.BOLD), ft.Container(padding=ft.padding.only(top=8), content=build_solution_grid(solution_cache))], spacing=8, tight=True)
            open_dialog(solution_dialog)
            return

        solution_dialog.content = ft.Column([ft.Text("Computing solution...", size=12, color=ft.Colors.GREY_700), ft.ProgressRing()], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True)
        open_dialog(solution_dialog)
        solution_dialog_gen += 1
        page.run_task(compute_solution_task, solution_dialog_gen)

    solution_btn.on_click = show_solution

    def show_graph(_=None):
        if current_mode != MODE_MANUAL:
            snack.content.value = "Graph is available only in Manual mode."
            snack.bgcolor = ft.Colors.RED_700
            snack.open = True
            page.update()
            return
        rows, cols = board.rows(), board.cols()
        nodes, edges = rows * cols, rows * (cols - 1) + (rows - 1) * cols
        graph_dialog.content = ft.Column([ft.Text(f"Nodes: {nodes}   Edges: {edges}", size=12, color=ft.Colors.GREY_700, weight=ft.FontWeight.BOLD), ft.Container(padding=ft.padding.only(top=8), content=build_graph_view(rows, cols, board.grid))], spacing=8, tight=True)
        open_dialog(graph_dialog)

    graph_btn.on_click = show_graph

    def set_status(msg: str, ok: bool):
        status.value = msg
        status.color = ft.Colors.GREEN_700 if ok else ft.Colors.RED_700

    def stop_computer_only():
        nonlocal ai_gen
        ai_gen += 1

    def stop_pvc_reply():
        nonlocal pvc_gen
        pvc_gen += 1

    def sync_input_lock():
        nonlocal input_locked
        input_locked = True if board.is_solved() else (current_mode == MODE_COMPUTER)

    def sync_pvc_counters_visibility():
        pvc_counters_row.visible = (current_mode == MODE_PVC)

    def sync_solution_visibility():
        solution_btn.visible = graph_btn.visible = (current_mode == MODE_MANUAL)

    def reset_counters():
        nonlocal moves, player_correct, computer_correct, wrong_black_removed
        moves = player_correct = computer_correct = wrong_black_removed = 0
        moves_text.value = "Moves: 0"
        timer_text.value = "CPU Time: 0.0000s"
        player_correct_text.value = "Player correct: 0"
        computer_correct_text.value = "Computer correct: 0"
        wrong_black_removed_text.value = "Wrong black removed: 0"

    def draw_board():
        grid_view.controls.clear()
        def faded_white(alpha: float):
            return ft.Colors.with_opacity(alpha, ft.Colors.WHITE)

        for r in range(board.rows()):
            row = ft.Row(spacing=0)
            for c in range(board.cols()):
                state, value = board.cell_state(r, c), board.value_at(r, c)
                row.controls.append(ft.Container(
                    width=CELL_SIZE, height=CELL_SIZE, alignment=ft.alignment.center,
                    bgcolor=ft.Colors.BLACK if state == CELL_BLACK else ft.Colors.WHITE,
                    border=ft.border.all(1, ft.Colors.BLUE_300),
                    content=ft.Text(str(value), color=faded_white(0.35) if state == CELL_BLACK else ft.Colors.BLACK, size=18, weight=ft.FontWeight.BOLD),
                    on_click=None if input_locked else (lambda e, r=r, c=c: on_cell_click(r, c)),
                    opacity=0.85 if input_locked else 1.0,
                ))
            grid_view.controls.append(row)

    def show_completed():
        nonlocal solved_shown, input_locked
        msg = "COMPLETED! Puzzle solved correctly."
        set_status(msg, True)
        if not solved_shown:
            snack.content.value = msg
            snack.open = True
            solved_shown = True
        input_locked = True
        completion_actions.visible = True

    async def computer_only_loop(gen: int):
        nonlocal moves

        # For D&C animation
        dc_target_state = None
        dc_queue = []
        
        # Accumulate pure CPU time
        total_cpu_time = 0.0

        while gen == ai_gen and current_mode == MODE_COMPUTER and not board.is_solved():
            
            moved = False

            if current_algorithm == ALGO_GREEDY:
                # MEASURE GREEDY STEP (STRICT CPU TIME)
                t_start = time.process_time()
                moved = board.greedy_move()
                t_end = time.process_time()
                
                total_cpu_time += (t_end - t_start)
            
            elif current_algorithm == ALGO_DC:
                # 1. Calculate solution if not yet done
                if dc_target_state is None:
                    try:
                        loop = asyncio.get_running_loop()
                        # MEASURE D&C CALCULATION (STRICT CPU TIME IN WORKER THREAD)
                        dc_target_state, dc_time = await loop.run_in_executor(None, run_dc_with_timer, board.grid)
                        
                        total_cpu_time = dc_time

                        # Build the diff queue (cells that need to change)
                        for r in range(board.rows()):
                            for c in range(board.cols()):
                                if board.cell_state(r, c) != dc_target_state[r][c]:
                                    dc_queue.append((r, c))
                    except Exception as e:
                        set_status(f"Error in D&C: {e}", False)
                        break
                
                # 2. Animate one step from the queue
                if dc_queue:
                    r, c = dc_queue.pop(0)
                    board.toggle_cell(r, c)
                    moved = True
            
            # Update timer display
            timer_text.value = f"CPU Time: {total_cpu_time:.6f}s"
            page.update()

            if not moved:
                set_status(f"{current_algorithm} finished/stuck.", False)
                completion_actions.visible = True
                sync_input_lock()
                draw_board()
                page.update()
                return

            moves += 1
            moves_text.value = f"Moves: {moves}"
            draw_board()

            if board.is_solved():
                show_completed()

            sync_input_lock()
            page.update()

            if board.is_solved():
                return
            await asyncio.sleep(0.5 if current_algorithm == ALGO_DC else 1.5)

    async def pvc_computer_reply(gen: int):
        nonlocal moves, computer_correct, wrong_black_removed
        await asyncio.sleep(0.2)
        if gen != pvc_gen or current_mode != MODE_PVC or board.is_solved():
            return
        ensure_solution_cache_started()

        black_before = count_black_cells()
        move_kind = pvc_correcting_move()
        black_after = count_black_cells()

        if move_kind is not None:
            moves += 1
            moves_text.value = f"Moves: {moves}"
            if move_kind == "added" and black_after > black_before:
                computer_correct += 1
                computer_correct_text.value = f"Computer correct: {computer_correct}"
            elif move_kind == "removed" and black_after < black_before:
                wrong_black_removed += 1
                wrong_black_removed_text.value = f"Wrong black removed: {wrong_black_removed}"
        else:
            set_status("Computer has no move.", False)

        draw_board()
        if board.is_solved():
            show_completed()
        else:
            issues = board.solve_issues()
            set_status("Not solved: " + ", ".join(issues), False)
        sync_input_lock()
        page.update()

    def start_computer_only():
        nonlocal ai_gen
        ai_gen += 1
        page.run_task(computer_only_loop, ai_gen)

    def reset_puzzle(_=None):
        nonlocal game, board, solved_shown, solution_dialog_gen, solution_cache_gen, solution_cache, solution_cache_started
        stop_computer_only()
        stop_pvc_reply()
        solution_dialog_gen += 1
        solution_cache_gen += 1
        solution_cache = None
        solution_cache_started = False

        game = Hitori()
        board = game.board()
        solved_shown = False
        snack.open = False
        completion_actions.visible = False
        reset_counters()
        set_status("", True)
        sync_pvc_counters_visibility()
        sync_solution_visibility()
        sync_input_lock()
        draw_board()
        page.update()

        if current_mode == MODE_PVC:
            ensure_solution_cache_started()
        if current_mode == MODE_COMPUTER:
            start_computer_only()

    def play_again(_=None):
        reset_puzzle()

    def change_mode(_=None):
        nonlocal solution_dialog_gen, solution_cache_gen, solution_cache, solution_cache_started
        solution_dialog_gen += 1
        solution_cache_gen += 1
        solution_cache = None
        solution_cache_started = False
        show_home()

    def on_cell_click(r, c):
        nonlocal moves, solved_shown, pvc_gen, player_correct
        if input_locked:
            return
        prev_state, before_score = board.cell_state(r, c), board.duplicate_conflict_score()
        board.toggle_cell(r, c)
        
        if not board.no_adjacent_black():
            board.toggle_cell(r, c)
            draw_board()
            set_status("Illegal move: adjacent black cells.", False)
            page.update()
            return

        if current_mode == MODE_PVC and prev_state == CELL_WHITE and board.cell_state(r, c) == CELL_BLACK:
            if board.duplicate_conflict_score() < before_score:
                player_correct += 1
                player_correct_text.value = f"Player correct: {player_correct}"

        moves += 1
        moves_text.value = f"Moves: {moves}"
        draw_board()
        if board.is_solved():
            show_completed()
            sync_input_lock()
            draw_board()
            page.update()
            return
        
        issues = board.solve_issues()
        set_status("Not solved: " + ", ".join(issues), False)
        solved_shown = False
        sync_input_lock()
        page.update()

        if current_mode == MODE_PVC:
            ensure_solution_cache_started()
            pvc_gen += 1
            page.run_task(pvc_computer_reply, pvc_gen)

    # ---------------- HOME UI ----------------
    mode_pick = ft.Dropdown(
        value=MODE_MANUAL, width=260,
        options=[ft.dropdown.Option(MODE_MANUAL), ft.dropdown.Option(MODE_COMPUTER), ft.dropdown.Option(MODE_PVC)],
        on_change=lambda e: update_algo_visibility()
    )
    
    algo_pick = ft.Dropdown(
        value=ALGO_GREEDY, width=260,
        label="Computer Strategy",
        visible=False,
        options=[ft.dropdown.Option(ALGO_GREEDY), ft.dropdown.Option(ALGO_DC)],
    )

    def update_algo_visibility():
        algo_pick.visible = (mode_pick.value == MODE_COMPUTER)
        page.update()

    def start_game(_=None):
        nonlocal current_mode, current_algorithm
        current_mode = mode_pick.value or MODE_MANUAL
        current_algorithm = algo_pick.value or ALGO_GREEDY
        show_game()

    start_btn = ft.ElevatedButton("Start", icon=ft.Icons.PLAY_ARROW, height=52, width=260, style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE, text_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD)), on_click=start_game)

    def show_home():
        stop_computer_only()
        stop_pvc_reply()
        mode_pick.value = current_mode
        update_algo_visibility()

        header = ft.Column([
            ft.Container(width=68, height=68, border_radius=22, bgcolor=ft.Colors.BLUE_600, alignment=ft.alignment.center, content=ft.Icon(ft.Icons.GRID_ON, size=34, color=ft.Colors.WHITE)),
            ft.Text("Welcome to Hitori", size=30, weight=ft.FontWeight.W_900, color=ft.Colors.BLUE_900, text_align=ft.TextAlign.CENTER),
            ft.Text("A logic puzzle where you shade cells to remove duplicates — without breaking the rules.", size=13, color=ft.Colors.GREY_700, text_align=ft.TextAlign.CENTER),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8)

        mode_card = ft.Container(
            width=360, gradient=ft.LinearGradient(begin=ft.alignment.top_left, end=ft.alignment.bottom_right, colors=[ft.Colors.WHITE, ft.Colors.BLUE_50]),
            border=ft.border.all(1, ft.Colors.BLUE_100), border_radius=16, padding=ft.padding.all(14),
            shadow=ft.BoxShadow(blur_radius=18, spread_radius=0, color=ft.Colors.BLACK12, offset=ft.Offset(0, 8)),
            content=ft.Column([
                ft.Text("Choose your mode", size=18, weight=ft.FontWeight.W_900, color=ft.Colors.BLUE_900, text_align=ft.TextAlign.CENTER),
                ft.Text("Pick how you want to play today.", size=13, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_800, text_align=ft.TextAlign.CENTER),
                ft.Text("Manual: you play • Computer-only: AI plays • Player with computer: take turns", size=12, color=ft.Colors.GREY_700, text_align=ft.TextAlign.CENTER),
                ft.Container(height=4),
                mode_pick,
                algo_pick,
                start_btn,
                ft.Text("Tip: Use the Manual 'Solution' button only when you're stuck.", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700, text_align=ft.TextAlign.CENTER),
            ], spacing=9, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        )

        rules_card = ft.Container(
            width=360, bgcolor=ft.Colors.BLUE_50, border=ft.border.all(1, ft.Colors.BLUE_100), border_radius=16, padding=ft.padding.all(14),
            content=ft.Column([
                ft.Text("Quick rules", size=16, weight=ft.FontWeight.W_800, color=ft.Colors.BLUE_900),
                ft.Row([ft.Icon(ft.Icons.LOOKS_ONE, size=18, color=ft.Colors.BLUE_800), ft.Text("No duplicates among white cells in any row/column.", size=12, color=ft.Colors.GREY_800)], spacing=10),
                ft.Row([ft.Icon(ft.Icons.LOOKS_TWO, size=18, color=ft.Colors.BLUE_800), ft.Text("No two black cells can touch (up/down/left/right).", size=12, color=ft.Colors.GREY_800)], spacing=10),
                ft.Row([ft.Icon(ft.Icons.LOOKS_3, size=18, color=ft.Colors.BLUE_800), ft.Text("All white cells must stay connected.", size=12, color=ft.Colors.GREY_800)], spacing=10),
                ft.Container(height=2),
                ft.Text("In Computer-only mode the AI makes one move every 2 seconds.", size=12, color=ft.Colors.GREY_700),
            ], spacing=9),
        )

        root.content = ft.Container(expand=True, alignment=ft.alignment.center, content=ft.Column([header, mode_card, rules_card], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12))
        page.update()

    # ---------------- GAME UI ----------------
    reset_btn = ft.ElevatedButton("Reset", icon=ft.Icons.REFRESH, on_click=reset_puzzle, height=44, style=ft.ButtonStyle(text_style=ft.TextStyle(size=15, weight=ft.FontWeight.BOLD)))
    play_again_btn = ft.ElevatedButton("Play again", icon=ft.Icons.REPLAY, on_click=play_again, height=44, style=ft.ButtonStyle(text_style=ft.TextStyle(size=15, weight=ft.FontWeight.BOLD)))
    change_mode_btn = ft.OutlinedButton("Change mode", icon=ft.Icons.SWAP_HORIZ, on_click=change_mode, height=44)
    completion_actions.controls = [reset_btn, play_again_btn, change_mode_btn]

    def show_game():
        nonlocal solved_shown
        solved_shown = False
        snack.open = False
        mode_label.value = f"Mode: {current_mode}" + (f" ({current_algorithm})" if current_mode == MODE_COMPUTER else "")
        completion_actions.visible = False
        set_status("", True)
        root.content = ft.Column([
            ft.Row([ft.Text("Hitori Puzzle", size=22, weight=ft.FontWeight.W_800, color=ft.Colors.BLUE_800)], alignment=ft.MainAxisAlignment.START),
            ft.Row([mode_label, ft.Row([solution_btn, graph_btn], spacing=8)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            pvc_counters_row,
            ft.Row([moves_text, timer_text], spacing=20),
            status,
            ft.Container(content=grid_view, expand=True, alignment=ft.alignment.top_center),
            completion_actions,
        ], spacing=12, expand=True)
        sync_pvc_counters_visibility()
        sync_solution_visibility()
        reset_puzzle()

    show_home()