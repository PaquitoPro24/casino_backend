from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from app.db.db_connect import get_connection
from psycopg2.extras import RealDictCursor
import datetime

router = APIRouter()

@router.post("/auditor/guardar")
async def guardar_auditoria(
    id_auditor: int = Form(...),
    resumen: str = Form(...),
    cumple: int = Form(...),
    no_cumple: int = Form(...),
    parcial: int = Form(...),
    no_aplica: int = Form(...),
    porcentaje: int = Form(...)
):
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            INSERT INTO Auditoria (id_auditor, fecha_auditoria, resumen)
            VALUES (%s, NOW(), %s)
            RETURNING id_auditoria;
        """, (id_auditor, resumen))

        id_auditoria = cursor.fetchone()['id_auditoria']

        cursor.execute("""
            INSERT INTO AuditoriaResultados
                (id_auditoria, cumple, no_cumple, parcial, no_aplica, porcentaje)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (id_auditoria, cumple, no_cumple, parcial, no_aplica, porcentaje))

        conn.commit()
        return {"message": "Auditoría guardada"}

    finally:
        cursor.close()
        conn.close()
