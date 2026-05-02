from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app import file_tools, ollama_client, agent, web_search, config

app = FastAPI(title="MCP Ollama Assistant", version="2.0")

# Request models
class AskRequest(BaseModel):
    question: str
    folder: str = "."
    allow_web: bool = False

class FileOperationRequest(BaseModel):
    path: str

class CreateFileRequest(BaseModel):
    path: str
    content: str
    overwrite: bool = False

class UpdateFileRequest(BaseModel):
    path: str
    content: str

class PatchFileRequest(BaseModel):
    path: str
    old_text: str
    new_text: str
    allow_multiple: bool = False

class AppendFileRequest(BaseModel):
    path: str
    content: str

class RenameFileRequest(BaseModel):
    old_path: str
    new_path: str

class DeleteFileRequest(BaseModel):
    path: str
    force: bool = False

class RestoreRequest(BaseModel):
    backup_path: str

class SearchRequest(BaseModel):
    query: str
    folder: str = "."

class AgentEditRequest(BaseModel):
    instruction: str
    target_files: Optional[List[str]] = None
    dry_run: bool = True

# Health check
@app.get("/")
def home():
    return {"status": "running", "version": "2.0"}

@app.get("/health")
def health():
    return {"success": True, "status": "healthy"}

# File listing
@app.get("/files")
def get_files(folder: str = "."):
    return file_tools.list_files(folder)

# File operations
@app.post("/files/read")
def post_read_file(req: FileOperationRequest):
    return file_tools.read_file(req.path)

@app.post("/files/search")
def post_search_files(req: SearchRequest):
    return file_tools.search_files(req.query, req.folder)

@app.post("/files/create")
def post_create_file(req: CreateFileRequest):
    return file_tools.create_file(req.path, req.content, req.overwrite)

@app.post("/files/update")
def post_update_file(req: UpdateFileRequest):
    return file_tools.update_file(req.path, req.content)

@app.post("/files/patch")
def post_patch_file(req: PatchFileRequest):
    return file_tools.patch_file(req.path, req.old_text, req.new_text, req.allow_multiple)

@app.post("/files/append")
def post_append_file(req: AppendFileRequest):
    return file_tools.append_to_file(req.path, req.content)

@app.post("/files/rename")
def post_rename_file(req: RenameFileRequest):
    return file_tools.rename_file(req.old_path, req.new_path)

@app.post("/files/delete")
def post_delete_file(req: DeleteFileRequest):
    return file_tools.delete_file(req.path, req.force)

@app.post("/files/restore")
def post_restore_file(req: RestoreRequest):
    return file_tools.restore_backup(req.backup_path)

# AI-powered endpoints
@app.post("/ask")
async def ask_about_files(req: AskRequest):
    """Enhanced ask endpoint with optional web search."""
    try:
        # Build context from files
        folder_result = file_tools.list_files(req.folder)
        if not folder_result["success"]:
            return folder_result

        context_parts = []
        file_count = 0

        for item in folder_result["data"]["items"]:
            if item["type"] == "file" and file_count < config.MAX_FILES_PER_REQUEST:
                file_path = f"{req.folder}/{item['name']}" if req.folder != "." else item['name']
                read_result = file_tools.read_file(file_path)
                if read_result["success"]:
                    content = read_result["data"]["content"][:config.MAX_FILE_CHARS]
                    context_parts.append(f"FILE: {file_path}\n{content}")
                    file_count += 1

        context = "\n\n".join(context_parts)

        # Check if web search is needed
        web_context = ""
        if req.allow_web and web_search.needs_fresh_info(req.question):
            search_result = await web_search.search_web(req.question)
            if search_result["success"]:
                web_context = web_search.summarize_web_results(search_result["results"])

        # Combine contexts
        full_context = f"{context}\n\n{web_context}" if web_context else context

        # Ask Ollama
        result = await ollama_client.ask_ollama(
            f"Question: {req.question}\n\nBased on the files and any web information provided:",
            full_context
        )

        if result["success"]:
            return {
                "success": True,
                "data": {
                    "answer": result["response"],
                    "used_web": bool(web_context),
                    "files_read": file_count
                }
            }
        else:
            return {"success": False, "error": result["error"]}

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/agent/edit")
async def agent_edit_endpoint(req: AgentEditRequest):
    return await agent.agent_edit(req.instruction, req.target_files, req.dry_run)

# Additional utility endpoints
@app.post("/files/summarize")
async def summarize_folder(folder: str = "."):
    """Summarize a folder using AI."""
    try:
        folder_result = file_tools.list_files(folder)
        if not folder_result["success"]:
            return folder_result

        files_content = {}
        for item in folder_result["data"]["items"]:
            if item["type"] == "file":
                file_path = f"{folder}/{item['name']}" if folder != "." else item['name']
                read_result = file_tools.read_file(file_path)
                if read_result["success"]:
                    files_content[file_path] = read_result["data"]["content"]

        summary = await ollama_client.summarize_folder(files_content)

        return {"success": True, "data": {"summary": summary}}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/files/explain")
async def explain_file_endpoint(req: FileOperationRequest):
    """Explain a file using AI."""
    try:
        read_result = file_tools.read_file(req.path)
        if not read_result["success"]:
            return read_result

        explanation = await ollama_client.explain_file(req.path, read_result["data"]["content"])

        return {"success": True, "data": {"explanation": explanation}}
    except Exception as e:
        return {"success": False, "error": str(e)}