from typing import List, Dict, Any, Optional
from app.file_tools import read_file
from app.ollama_client import propose_edits
from app.safety import safe_path
from pathlib import Path

async def agent_edit(instruction: str, target_files: Optional[List[str]] = None, dry_run: bool = True) -> Dict[str, Any]:
    """AI-driven edit proposal and execution."""
    try:
        # Determine which files to examine
        if not target_files:
            # Auto-detect relevant files based on instruction
            target_files = await _detect_relevant_files(instruction)

        # Read target files
        file_contents = {}
        for file_path in target_files[:10]:  # Limit files
            result = read_file(file_path)
            if result["success"]:
                file_contents[file_path] = result["data"]["content"]
            else:
                file_contents[file_path] = f"Error reading file: {result['error']}"

        # Get AI proposal
        proposal_result = await propose_edits(instruction, file_contents)
        if not proposal_result["success"]:
            return {"success": False, "error": f"Failed to generate proposal: {proposal_result['error']}"}

        proposal = proposal_result["proposal"]

        response = {
            "success": True,
            "data": {
                "instruction": instruction,
                "target_files": target_files,
                "proposal": proposal,
                "dry_run": dry_run,
                "risks": _assess_risks(instruction, target_files)
            }
        }

        if not dry_run:
            # In a real implementation, you'd parse the proposal and apply changes
            # For now, just indicate that changes would be applied
            response["data"]["applied"] = False  # Placeholder
            response["message"] = "Changes would be applied (implementation needed)"

        return response

    except Exception as e:
        return {"success": False, "error": str(e)}

async def _detect_relevant_files(instruction: str) -> List[str]:
    """Detect which files are relevant to the instruction."""
    # Simple heuristic - in a real implementation, you might use AI for this
    keywords = instruction.lower().split()
    relevant_files = []

    # Common file patterns
    patterns = {
        "python": ["*.py"],
        "javascript": ["*.js", "*.ts", "*.jsx", "*.tsx"],
        "config": ["*.json", "*.yaml", "*.yml", "Dockerfile", "*.toml"],
        "docs": ["*.md", "README*"]
    }

    # This is a simplified version - you'd want more sophisticated detection
    return ["server.py", "requirements.txt", "Dockerfile"]  # Default fallback

def _assess_risks(instruction: str, target_files: List[str]) -> List[str]:
    """Assess potential risks of the changes."""
    risks = []

    if any("delete" in instruction.lower() for instruction in [instruction]):
        risks.append("Instruction mentions deletion - ensure backups are created")

    if len(target_files) > 5:
        risks.append("Many files targeted - review changes carefully")

    if any(file.endswith((".env", "config.json", "settings.py")) for file in target_files):
        risks.append("Configuration files targeted - changes may affect system behavior")

    return risks if risks else ["Low risk - standard code changes"]