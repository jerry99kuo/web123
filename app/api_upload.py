from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from sqlmodel import Session, delete

from app.models import Puzzle, get_session

router = APIRouter()

class PuzzleData(BaseModel):
    question: str
    answer: List[str] 

# 🌟 在參數加上 mode: str = "append"，預設為附加模式
@router.post("/upload")
async def receive_puzzles(
    puzzles: List[PuzzleData], 
    mode: str = "append", 
    session: Session = Depends(get_session)
):
    print(f"[Success] 收到 {len(puzzles)} 筆資料，當前模式：{mode}")
    
    # 【功能 1：Overwrite 覆蓋模式】
    # 如果 C++ 傳來時指定要覆蓋，就先砍掉資料庫裡所有舊的謎題
    if mode == "overwrite":
        session.exec(delete(Puzzle))
        session.commit()
        print("🗑️ 已清空資料庫中的舊謎題。")
    
    count = 0
    for p in puzzles:
        # 🧹 【清理炸彈 1 & 2】移除頭尾多餘的雙引號 (")，並清掉空白
        clean_question = p.question.strip().strip('"')
        
        # 如果清乾淨後發現它是表頭 ("Board")，或者是空的，就直接跳過不存
        if clean_question == "Board" or not clean_question:
            continue
            
        # 處理 Answer 陣列，一樣把雙引號清乾淨
        clean_answers = [ans.strip().strip('"') for ans in p.answer]
        solution_str = "   ".join(clean_answers) if clean_answers else "no solution"
        
        # 寫入乾淨的資料
        new_puzzle = Puzzle(board_str=clean_question, solution=solution_str)
        session.add(new_puzzle)
        count += 1
        
    session.commit()
    
    action_msg = "覆蓋並寫入" if mode == "overwrite" else "附加了"
    return {
        "status": "success", 
        "message": f"成功{action_msg} {count} 筆謎題至資料庫。"
    }