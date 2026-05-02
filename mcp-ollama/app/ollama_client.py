import httpx
from typing import Optional, Dict, Any
from app.config import OLLAMA_HOST, OLLAMA_MODEL, MAX_TOTAL_CONTEXT_CHARS

async def ask_ollama(prompt: str, context: str = "", model: Optional[str] = None) -> Dict[str, Any]:
    """Ask Ollama a question with optional context."""
    if model is None:
        model = OLLAMA_MODEL

    # Limit context size
    if context:
        context = context[:MAX_TOTAL_CONTEXT_CHARS]

    full_prompt = f"{context}\n\n{prompt}" if context else prompt

    async with httpx.AsyncClient(timeout=180) as client:
        try:
            response = await client.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": model,
                    "prompt": full_prompt,
                    "stream": False,
                },
            )
            result = response.json()
            return {"success": True, "response": result.get("response", "")}
        except Exception as e:
            return {"success": False, "error": str(e)}

async def summarize_folder(files_content: Dict[str, str]) -> str:
    """Ask Ollama to summarize a folder based on file contents."""
    if not files_content:
        return "Empty folder"

    context = "\n\n".join([f"File: {path}\n{content[:2000]}" for path, content in files_content.items()])
    context = context[:MAX_TOTAL_CONTEXT_CHARS]

    prompt = f"""
Summarize this project folder based on the files below. Focus on:
- What the project does
- Main technologies used
- Key files and their purposes
- Overall architecture

Files:
{context}
"""

    result = await ask_ollama(prompt)
    return result.get("response", "Summary not available") if result["success"] else "Error generating summary"

async def explain_file(file_path: str, content: str) -> str:
    """Ask Ollama to explain a file."""
    content = content[:MAX_TOTAL_CONTEXT_CHARS]

    prompt = f"""
Explain this file in simple terms. What does it do? How does it work?

File: {file_path}
Content:
{content}
"""

    result = await ask_ollama(prompt)
    return result.get("response", "Explanation not available") if result["success"] else "Error generating explanation"

async def propose_edits(instruction: str, target_files: Dict[str, str]) -> Dict[str, Any]:
    """Ask Ollama to propose edits based on an instruction."""
    context = "\n\n".join([f"File: {path}\n{content[:3000]}" for path, content in target_files.items()])
    context = context[:MAX_TOTAL_CONTEXT_CHARS]

    prompt = f"""
Based on the instruction and current files, propose exact changes to implement the requested feature.

Instruction: {instruction}

Current files:
{context}

Please respond with:
1. Summary of changes needed
2. Files to modify and specific changes (use diff format if possible)
3. Potential risks or considerations

Be precise and safe with your suggestions.
"""

    result = await ask_ollama(prompt)
    if result["success"]:
        return {"success": True, "proposal": result["response"]}
    else:
        return {"success": False, "error": result["error"]}