# app/routers/prompts.py
"""
Prompt Storage API
"""
import json
import uuid
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/prompts", tags=["prompts"])

STORAGE_DIR = Path("storage")
PROMPTS_FILE = STORAGE_DIR / "prompts.json"


class PromptCreate(BaseModel):
    """Schema for creating a new prompt."""
    name: str
    content: str


class PromptResponse(BaseModel):
    """Schema for prompt response."""
    id: str
    name: str
    content: str


def _ensure_storage() -> None:
    """Ensure storage directory and file exist."""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    if not PROMPTS_FILE.exists():
        PROMPTS_FILE.write_text("[]", encoding="utf-8")


def _load_prompts() -> List[Dict[str, Any]]:
    """Load prompts from storage file."""
    _ensure_storage()
    try:
        return json.loads(PROMPTS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _save_prompts(prompts: List[Dict[str, Any]]) -> None:
    """Save prompts to storage file."""
    _ensure_storage()
    PROMPTS_FILE.write_text(json.dumps(prompts, ensure_ascii=False, indent=2), encoding="utf-8")


@router.get("", response_model=List[PromptResponse])
async def get_prompts() -> List[Dict[str, Any]]:
    """Get all saved prompts."""
    return _load_prompts()


@router.post("", response_model=PromptResponse)
async def create_prompt(prompt: PromptCreate) -> Dict[str, Any]:
    """Create a new prompt."""
    prompts = _load_prompts()
    new_prompt = {
        "id": str(uuid.uuid4()),
        "name": prompt.name,
        "content": prompt.content
    }
    prompts.append(new_prompt)
    _save_prompts(prompts)
    return new_prompt


@router.delete("/{prompt_id}")
async def delete_prompt(prompt_id: str) -> Dict[str, str]:
    """Delete a prompt by ID."""
    prompts = _load_prompts()
    original_count = len(prompts)
    prompts = [p for p in prompts if p.get("id") != prompt_id]
    
    if len(prompts) == original_count:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    _save_prompts(prompts)
    return {"message": "Prompt deleted successfully"}
