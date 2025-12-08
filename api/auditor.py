from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
import os

# Simple auth dependency using cookies
async def get_current_user_from_cookie(request: Request):
    user_id = request.cookies.get("userId")
    if not user_id:
        raise HTTPException(status_code=401, detail="No autenticado")
    return {"id_usuario": int(user_id)}

router = APIRouter(prefix="/api", tags=["Auditor"])

# Modelos Pydantic
class AuditoriaRequest(BaseModel):
    fecha: str
    respuestas: Dict[str, str]

class AuditoriaResponse(BaseModel):
    exito: bool
    mensaje: str
    pdf_url: Optional[str] = None

# Directorio para PDFs
PDF_DIR = "pdfs_auditorias"
os.makedirs(PDF_DIR, exist_ok=True)

@router.post("/guardar_checklist", response_model=AuditoriaResponse)
async def guardar_checklist(
    auditoria: AuditoriaRequest,
    current_user: dict = Depends(get_current_user_from_cookie)
):
    """Guardar checklist de auditoría y generar PDF"""
    try:
        from .db_config import get_db_connection
        
        # Calcular estadísticas
        cumple = sum(1 for v in auditoria.respuestas.values() if v == "Cumple")
        no_cumple = sum(1 for v in auditoria.respuestas.values() if v == "No Cumple")
        parcial = sum(1 for v in auditoria.respuestas.values() if v == "Cumple Parcialmente")
        no_aplica = sum(1 for v in auditoria.respuestas.values() if v == "No Aplica")
        
        total_respondidas = cumple + no_cumple + parcial
        porcentaje = round(((cumple + (parcial * 0.5)) / total_respondidas) * 100) if total_respondidas > 0 else 0
        
        # Guardar en base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        
        datos_json = {
            "cumple": cumple,
            "no_cumple": no_cumple,
            "parcial": parcial,
            "no_aplica": no_aplica,
            "porcentaje_cumplimiento": porcentaje,
            "respuestas": auditoria.respuestas
        }
        
        cursor.execute("""
            INSERT INTO auditoria (id_usuario, resumen, datos_auditoria)
            VALUES (%s, %s, %s)
            RETURNING id_auditoria
        """, (
            current_user["id_usuario"],
            f"Auditoría ISO 14001 - Cumplimiento: {porcentaje}%",
            json.dumps(datos_json)
        ))
        
        id_auditoria = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        # Generar PDF
        pdf_filename = f"auditoria_{id_auditoria}.pdf"
        pdf_path = os.path.join(PDF_DIR, pdf_filename)
        
        generar_pdf_auditoria(
            pdf_path,
            id_auditoria,
            auditoria.fecha,
            auditoria.respuestas,
            cumple,
            no_cumple,
            parcial,
            no_aplica,
            porcentaje
        )
        
        return AuditoriaResponse(
            exito=True,
            mensaje="Auditoría guardada exitosamente",
            pdf_url=f"/api/pdf_auditoria/{id_auditoria}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar auditoría: {str(e)}")

@router.get("/auditor/historial")
async def obtener_historial(current_user: dict = Depends(get_current_user_from_cookie)):
    """Obtener historial de auditorías del usuario"""
    try:
        from .db_config import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id_auditoria, fecha_auditoria, resumen, datos_auditoria
            FROM auditoria
            WHERE id_usuario = %s
            ORDER BY fecha_auditoria DESC
        """, (current_user["id_usuario"],))
        
        auditorias = []
        for row in cursor.fetchall():
            datos = json.loads(row[3]) if isinstance(row[3], str) else row[3]
            auditorias.append({
                "id_auditoria": row[0],
                "fecha_auditoria": row[1].isoformat(),
                "resumen": row[2],
                "datos_auditoria": datos
            })
        
        cursor.close()
        conn.close()
        
        return {"historial": auditorias}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener historial: {str(e)}")

@router.get("/pdf_auditoria/{id_auditoria}")
async def descargar_pdf(
    id_auditoria: int,
    current_user: dict = Depends(get_current_user_from_cookie)
):
    """Descargar PDF de auditoría"""
    try:
        pdf_filename = f"auditoria_{id_auditoria}.pdf"
        pdf_path = os.path.join(PDF_DIR, pdf_filename)
        
        if not os.path.exists(pdf_path):
            # Si no existe, regenerar
            from .db_config import get_db_connection
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT datos_auditoria, fecha_auditoria
                FROM auditoria
                WHERE id_auditoria = %s AND id_usuario = %s
            """, (id_auditoria, current_user["id_usuario"]))
            
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Auditoría no encontrada")
            
            datos = json.loads(row[0]) if isinstance(row[0], str) else row[0]
            fecha = row[1].strftime("%Y-%m-%d")
            
            generar_pdf_auditoria(
                pdf_path,
                id_auditoria,
                fecha,
                datos.get("respuestas", {}),
                datos.get("cumple", 0),
                datos.get("no_cumple", 0),
                datos.get("parcial", 0),
                datos.get("no_aplica", 0),
                datos.get("porcentaje_cumplimiento", 0)
            )
            
            cursor.close()
            conn.close()
        
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=pdf_filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar PDF: {str(e)}")

def generar_pdf_auditoria(
    pdf_path: str,
    id_auditoria: int,
    fecha: str,
    respuestas: Dict[str, str],
    cumple: int,
    no_cumple: int,
    parcial: int,
    no_aplica: int,
    porcentaje: int
):
    """Generar PDF de auditoría con ReportLab"""
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    
    # Colores
    dorado = HexColor("#ab925c")
    negro = HexColor("#1a1a1a")
    gris = HexColor("#666666")
    
    # Header
    c.setFillColor(dorado)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width/2, height - 50, "Auditoría ISO 14001")
    
    c.setFillColor(gris)
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, height - 70, "Royal Crumbs Casino")
    c.drawCentredString(width/2, height - 85, f"Fecha: {fecha}")
    c.drawCentredString(width/2, height - 100, f"Reporte #{id_auditoria}")
    
    # Línea separadora
    c.setStrokeColor(dorado)
    c.line(50, height - 110, width - 50, height - 110)
    
    y = height - 140
    
    # Respuestas
    c.setFillColor(negro)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Resultados de la Auditoría:")
    y -= 25
    
    c.setFont("Helvetica", 9)
    for i, (pregunta, respuesta) in enumerate(respuestas.items(), 1):
        if y < 100:
            c.showPage()
            y = height - 50
        
        # Pregunta
        c.setFillColor(dorado)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(50, y, f"{i}.")
        
        # Wrap text
        c.setFillColor(negro)
        c.setFont("Helvetica", 8)
        pregunta_lines = []
        words = pregunta.split()
        line = ""
        for word in words:
            test_line = line + word + " "
            if c.stringWidth(test_line, "Helvetica", 8) < width - 120:
                line = test_line
            else:
                pregunta_lines.append(line)
                line = word + " "
        pregunta_lines.append(line)
        
        for line in pregunta_lines:
            c.drawString(70, y, line)
            y -= 10
        
        # Respuesta
        if respuesta == "Cumple":
            c.setFillColor(HexColor("#00aa00"))
        elif respuesta == "No Cumple":
            c.setFillColor(HexColor("#cc0000"))
        elif respuesta == "Cumple Parcialmente":
            c.setFillColor(HexColor("#ff9900"))
        else:
            c.setFillColor(gris)
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(70, y, f"→ {respuesta}")
        y -= 20
    
    # Resumen en nueva página
    c.showPage()
    y = height - 50
    
    c.setFillColor(dorado)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width/2, y, "Resumen de Resultados")
    y -= 40
    
    c.setFont("Helvetica", 14)
    c.setFillColor(HexColor("#00aa00"))
    c.drawString(100, y, f"✓ Cumple: {cumple}")
    y -= 25
    
    c.setFillColor(HexColor("#cc0000"))
    c.drawString(100, y, f"✗ No Cumple: {no_cumple}")
    y -= 25
    
    c.setFillColor(HexColor("#ff9900"))
    c.drawString(100, y, f"⚠ Cumple Parcialmente: {parcial}")
    y -= 25
    
    c.setFillColor(gris)
    c.drawString(100, y, f"− No Aplica: {no_aplica}")
    y -= 40
    
    c.setFillColor(dorado)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, y, f"Cumplimiento Total: {porcentaje}%")
    
    c.save()
