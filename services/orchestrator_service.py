import traceback
import httpx
from fastapi import UploadFile, HTTPException
from models.user_models import UserData
from utils.logger import logger
from dotenv import load_dotenv
import os

#load_dotenv()

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL")
USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL")
DOCUMENTS_SERVICE_URL = os.getenv("DOCUMENTS_SERVICE_URL")
REGISTRADURIA_API = os.getenv("REGISTRADURIA_API")

async def process_registration(user_data: UserData, document: UploadFile):
    logger.info(f"→ Iniciando registro para usuario ID: {user_data.user_id}")
    logger.info(f"→ Llamando a AUTH en: {AUTH_SERVICE_URL}/")

    async with httpx.AsyncClient() as client:
        # Verificación con AUTH
        try:
            auth_payload = {"id": user_data.user_id, "email":user_data.email, "password": user_data.password}
            response = await client.post(f"{AUTH_SERVICE_URL}/validate", json=auth_payload, timeout=30)
            logger.info(f"← Respuesta AUTH: {response.status_code}")

            if response.status_code == 422:
                # Extraemos el mensaje original de AUTH y lo reenviamos
                detail = response.json().get("detail", "Error de validación en auth.")
                logger.warning(f"Authentication rechazado por validación, contraseña poco segura: {detail}")
                raise HTTPException(status_code=422, detail=detail)

            logger.info(f"← Respuesta AUTH: {response.status_code}")

            if response.status_code == 421:
                # ID inválido, simplemente pasa el error al frontend
                raise HTTPException(
                    status_code=422,
                    detail="ID inválido. Debe tener al menos 10 dígitos."
                )

            if response.status_code == 200:
                logger.warning("Usuario ya está registrado. Deteniendo proceso.")
                raise HTTPException(
                    status_code=409,
                    detail="El usuario ya está registrado en el sistema."
                )

            elif response.status_code != 204:
                logger.error(f"⛔ Error inesperado de AUTH: {response.status_code}")
                raise HTTPException(
                    status_code=502,
                    detail="Error verificando identidad con la Registraduría."
                )
        except Exception as e:
            logger.debug(traceback.format_exc())
            logger.error(f"Error conectando con AUTH: {repr(e)}")
            raise HTTPException(status_code=503, detail=repr(e))

        # Registro con USERS
        try:
            logger.info("→ Enviando solicitud de creación a USERS")
            user_payload = user_data.dict()
            user_payload.pop("password", None)
            response = await client.post(f"{USERS_SERVICE_URL}/create", json=user_payload,timeout=30)
            logger.info(f"← Respuesta USERS: {response.status_code}")
            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail="Error en la creación del usuario en el microservicio USERS."
                )
        except Exception as e:
            logger.error(f"Error conectando con USERS: {repr(e)}")
            logger.info(traceback.format_exc())
            raise HTTPException(status_code=503, detail=repr(e))
        

        payload = {
        "email": user_data.email,
        "password": user_data.password}
    
        try:
            response = await client.post(f"{AUTH_SERVICE_URL}/login", json=payload)

            logger.info(f"← Response status: {response.status_code}")
            logger.info(f"← Response body: {response.text}")

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Access Token: {data['access_token']}")
            else:
                logger.error(f"⛔ Login failed: {response.status_code} - {response.text}")
        except httpx.RequestError as e:
            logger.error(f"⚠️ HTTPX Request Error: {repr(e)}")
            raise e
        
        try:
            logger.info(f"→ Enviando solicitud de creación a DOCUMENTS: {DOCUMENTS_SERVICE_URL}")
            file_bytes = await document.read()  # Read content from UploadFile

            files = {
            'file': (document.filename, file_bytes, document.content_type)
            }
            
            response = await client.put(f"{DOCUMENTS_SERVICE_URL}/doc/{user_data.user_id}/cedula_de_ciudadania.{document.filename.split('.')[1]}",files=files,headers={"Authorization" : "bearer " + data['access_token']},timeout=30)
            logger.info(f"← Respuesta DOCUMENTS: {response.status_code}")

        except Exception as e:
            logger.debug(traceback.format_exc())
            logger.error(f"Error conectando con DOCUMENTS: {repr(e)}")
            raise HTTPException(status_code=503, detail=str(repr(e)))

    return {"access_token" : data['access_token'], "token_type": "bearer"}



async def sign_document(document_id, document_name, document_path, user_id):
    logger.info(f"→ Iniciando firma para el documento ID: {document_id}")
    logger.info(f"→ Llamando a DOCUMENTS en: {DOCUMENTS_SERVICE_URL}/")

    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Searching for document url: {response_signed_url}")
            response_signed_url = await client.post(f"{DOCUMENTS_SERVICE_URL}/docs/signed-urls",json={"document_paths": [document_path]})
            data_urls_dict = response_signed_url.json()
            logger.info(f"← Respuesta DOCUMENTS: {response_signed_url}")
            

            logger.info(f"Updating document sign metadata: {response_signed_url}")
            response_sign_metadata = await client.patch(f"{DOCUMENTS_SERVICE_URL}/metadata/{document_id}/sign")
            logger.info(f"← Respuesta DOCUMENTS: {response.status_code}")

            logger.info(f"Reporting to external URL: {response_signed_url}")
            response = await client.post(f"{REGISTRADURIA_API}/authenticateDocument", 
                                         json={"id_citizen":user_id, "urlDocument": response_signed_url["signed_urls"][0], "document_title": document_name})
            
            if response.status_code == 200:
                return {"message": "Documento firmado y reportado exitosamente."}
            else:
                raise HTTPException(status_code=500, detail="Error firmando el documento.")

        except Exception as e:
            logger.error(f"Error conectando con DOCUMENTS: {repr(e)}")
            raise HTTPException(status_code=503, detail=str(repr(e)))
        


async def get_operators():
     async with httpx.AsyncClient() as client:
        try:
            response_get_operators = await client.get(f"{REGISTRADURIA_API}/getOperators")
        except Exception as e:
            logger.error(f"Error conectando con api externa: {e}")
            raise e
        
        response_get_operators = response_get_operators.json()
        filtered_list = [item for item in response_get_operators if "transferAPIURL" in item]
        for item in filtered_list:
            print(item["operatorName"], "->", item["transferAPIURL"])
        return filtered_list