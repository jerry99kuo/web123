from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List
from sqlmodel import Session, select
from app.models import Puzzle, get_session

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# ==============================================================================
# 全域遊戲狀態
# ==============================================================================
game_state = {
    "current_puzzle_id": None,
    "board": [[None for _ in range(6)] for _ in range(6)],
    "turn": "blue",
    "status": "playing", 
    "message": "請選擇一個謎題開始！",
    "solution_steps": [],     
    "current_step_index": 0   
}

# ==============================================================================
# 解析工具
# ==============================================================================
def parse_board_string(board_str: str):
    board = [[None for _ in range(6)] for _ in range(6)]
    for i, char in enumerate(board_str):
        if char == '.': continue
        r, c = i // 6, i % 6
        if char == 'B': board[r][c] = {"player": "blue", "type": "good"}
        elif char == 'R': board[r][c] = {"player": "blue", "type": "bad"}
        elif char == 'b': board[r][c] = {"player": "red", "type": "good"}
        elif char == 'r': board[r][c] = {"player": "red", "type": "bad"}
    return board

def parse_solution_steps(solution_str: str):
    if solution_str == "no solution" or not solution_str:
        return []
    
    steps = solution_str.split("   ")
    parsed_steps = []
    
    for step in steps:
        parts = step.strip().split()
        if len(parts) >= 4:
            piece, pos, direction = parts[1], parts[2], parts[3]
            from_c = ord(pos[0]) - ord('a')
            from_r = 6 - int(pos[1])
            to_c, to_r = from_c, from_r
            if direction == 'up': to_r -= 1
            elif direction == 'down': to_r += 1
            elif direction == 'left': to_c -= 1
            elif direction == 'right': to_c += 1
                
            parsed_steps.append({
                "player": "blue" if piece.isupper() else "red",
                "from_row": from_r, "from_col": from_c,
                "to_row": to_r, "to_col": to_c
            })
    return parsed_steps

# ==============================================================================
# API 資料驗證模型
# ==============================================================================
class MovePayload(BaseModel):
    from_row: int
    from_col: int
    to_row: int
    to_col: int
    player: str

class RatePayload(BaseModel):
    puzzle_id: str
    rating: int


@router.get("/api/chess/puzzles")
async def get_all_puzzles(session: Session = Depends(get_session)):
    """提供前端動態產生下拉選單"""
    puzzles = session.exec(select(Puzzle)).all()
    return {"puzzles": [{"id": p.id, "title": f"謎題 #{p.id:03d}"} for p in puzzles]}

@router.post("/api/chess/load_puzzle/{puzzle_id}")
async def load_puzzle(puzzle_id: int, session: Session = Depends(get_session)):
    """從資料庫讀取謎題載入遊戲"""
    puzzle = session.get(Puzzle, puzzle_id)
    if not puzzle:
        return JSONResponse(status_code=404, content={"message": "找不到該謎題"})
    
    game_state["current_puzzle_id"] = str(puzzle_id)
    game_state["board"] = parse_board_string(puzzle.board_str)
    game_state["solution_steps"] = parse_solution_steps(puzzle.solution)
    game_state["current_step_index"] = 0
    
    if puzzle.solution == "no solution" or not game_state["solution_steps"]:
        game_state["status"] = "failed"
        game_state["message"] = "💀 警告：此局無解！"
    else:
        game_state["status"] = "playing"
        game_state["turn"] = game_state["solution_steps"][0]["player"]
        game_state["message"] = f"挑戰開始！ (需執行 {len(game_state['solution_steps'])} 步)"
        
    return {"message": "載入成功"}

@router.get("/api/chess/solution/{puzzle_id}")
async def get_solution(puzzle_id: int, session: Session = Depends(get_session)):
    puzzle = session.get(Puzzle, puzzle_id)
    if not puzzle:
        return JSONResponse(status_code=404, content={"message": "無此謎題"})
    return {"solution": puzzle.solution}

# (其餘原有的頁面渲染、移動、自動下棋、評分 API 保持不變)
@router.get("/chess", response_class=HTMLResponse)
async def get_chess_page(request: Request):
    return templates.TemplateResponse(request = request, name = "chess.html", context={"request": request})

@router.get("/api/chess/board")
async def get_board(player: str):
    visible_board = []
    for r in range(6):
        row_data = []
        for c in range(6):
            piece = game_state["board"][r][c]
            if piece is None:
                row_data.append(None)
            else:
                if piece["player"] == player or game_state["status"] != "playing":
                    row_data.append(piece)
                else:
                    row_data.append({"player": piece["player"], "type": "unknown"})
        visible_board.append(row_data)
    return {
        "board": visible_board, "turn": game_state["turn"],
        "status": game_state["status"], "message": game_state["message"],
        "puzzle_title": f"謎題 #{int(game_state['current_puzzle_id']):03d}" if game_state["current_puzzle_id"] else "未載入"
    }

@router.post("/api/chess/move")
async def move_piece(payload: MovePayload):
    if game_state["status"] != "playing":
        return JSONResponse(status_code=400, content={"message": "謎題已結束！"})
    if payload.player != game_state["turn"]:
        return JSONResponse(status_code=400, content={"message": "請等待對手動作！"})
        
    expected = game_state["solution_steps"][game_state["current_step_index"]]
    if (payload.from_row != expected["from_row"] or payload.from_col != expected["from_col"] or
        payload.to_row != expected["to_row"] or payload.to_col != expected["to_col"]):
        return JSONResponse(status_code=400, content={"message": "❌ 這步走錯了！再仔細想想最佳路徑！"})

    board = game_state["board"]
    piece = board[payload.from_row][payload.from_col]
    board[payload.from_row][payload.from_col] = None
    
    is_escaping = payload.to_col < 0 or payload.to_col > 5 or payload.to_row < 0 or payload.to_row > 5
    if not is_escaping:
        board[payload.to_row][payload.to_col] = piece

    game_state["current_step_index"] += 1
    
    if game_state["current_step_index"] >= len(game_state["solution_steps"]):
        game_state["status"] = "solved"
        game_state["message"] = "🎉 完美解開謎題！好鬼成功逃出生天！"
    else:
        game_state["turn"] = game_state["solution_steps"][game_state["current_step_index"]]["player"]
        game_state["message"] = "移動正確！等待敵方回應..."
    return {"status": "success"}

@router.post("/api/chess/auto_move")
async def auto_move():
    if game_state["status"] != "playing" or game_state["turn"] != "red":
        return {"status": "ignored"}
        
    expected = game_state["solution_steps"][game_state["current_step_index"]]
    board = game_state["board"]
    piece = board[expected["from_row"]][expected["from_col"]]
    board[expected["from_row"]][expected["from_col"]] = None
    board[expected["to_row"]][expected["to_col"]] = piece

    game_state["current_step_index"] += 1
    game_state["turn"] = "blue"
    game_state["message"] = "敵方已行動！輪到你了！"
    return {"status": "success"}

@router.post("/api/chess/rate")
async def rate_puzzle(payload: RatePayload):
    return {"message": "感謝您的評分！"}