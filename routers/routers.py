# orchestrator/routes/register.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from services.orchestrator_service import process_registration, sign_document
from models.user_models import UserData, AuthDoc
from services.token_service import verify_token
from fastapi import Depends
import json

router = APIRouter()

@router.post("/register")
async def register_user(data: str = Form(...), document: UploadFile = File(...)):
    try:
        user_data = UserData(**json.loads(data))
        print("PARSED DATA:", user_data)
        result = await process_registration(user_data, document)
        return result
    except HTTPException as http_exc:
        raise http_exc  # ← Re-lanza excepciones HTTP personalizadas como están
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    
@router.post("/authenticate_doc")
async def auth_doc(data: AuthDoc, payload: dict = Depends(verify_token)):
    return await sign_document(document_id= data.document_id, document_name=data.document_name, document_path=data.document_path, user_id=payload['sub'])
