import httpx
from fastapi import UploadFile, HTTPException
from models.user_models import UserData
from utils.logger import logger
from dotenv import load_dotenv
import os

load_dotenv()

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL")
USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL")

async def process_registration(user_data: UserData, document: UploadFile):
    logger.info(f"→ Iniciando registro para usuario ID: {user_data.id}")
    logger.info(f"→ Llamando a AUTH en: {AUTH_SERVICE_URL}/")

    async with httpx.AsyncClient() as client:
        # Verificación con AUTH
        try:
            auth_payload = {"id": user_data.id, "email":user_data.email, "password": user_data.password}
            response = await client.post(f"{AUTH_SERVICE_URL}/", json=auth_payload)
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
        except httpx.RequestError as e:
            logger.error(f"Error conectando con AUTH: {e}")
            raise HTTPException(status_code=503, detail=str(e))

        # Registro con USERS
        try:
            logger.info("→ Enviando solicitud de creación a USERS")
            user_payload = user_data.dict()
            user_payload.pop("password", None)
            response = await client.post(USERS_SERVICE_URL, json=user_payload)
            logger.info(f"← Respuesta USERS: {response.status_code}")

            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail="Error en la creación del usuario en el microservicio USERS."
                )

        except httpx.RequestError as e:
            logger.error(f"Error conectando con USERS: {e}")
            raise HTTPException(status_code=503, detail=str(e))

    return {"message": "Registro completado exitosamente."}
