"""
🔌 TICKET API - API REST pour la gestion des tickets
Accessible depuis le dashboard web admin
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import jwt
import os

app = FastAPI(title="Maxis Ticket API", version="1.0")
security = HTTPBearer()

# Modèles Pydantic
class TicketCreate(BaseModel):
    user_id: int
    guild_id: int
    subject: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=10)
    category: str = Field(default="general")
    priority: str = Field(default="medium")

class TicketReply(BaseModel):
    content: str = Field(..., min_length=1)
    is_internal: bool = Field(default=False)

class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[int] = None

class TicketResponse(BaseModel):
    id: str
    user_id: int
    subject: str
    description: str
    category: str
    priority: str
    status: str
    assigned_to: Optional[int]
    created_at: datetime
    updated_at: datetime
    messages_count: int = 0

# Authentification JWT
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Vérifie le token JWT admin"""
    try:
        payload = jwt.decode(
            credentials.credentials,
            os.getenv('JWT_SECRET', 'secret-key'),
            algorithms=['HS256']
        )
        if payload.get('role') != 'admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Endpoints
@app.get("/api/tickets", response_model=List[TicketResponse])
async def get_all_tickets(
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    category: Optional[str] = Query(None, description="Filter by category"),
    assigned_to: Optional[int] = Query(None, description="Filter by assignee"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin: dict = Depends(verify_token)
):
    """
    Récupère tous les tickets (admin only)
    Avec filtres et pagination
    """
    # Ici, tu appellerais ta DB Supabase
    # Exemple simplifié:
    
    # db = get_supabase_client()
    # query = db.table('tickets').select('*')
    # 
    # if status:
    #     query = query.eq('status', status)
    # if priority:
    #     query = query.eq('priority', priority)
    # ...
    
    return []  # À implémenter avec Supabase

@app.get("/api/tickets/{ticket_id}")
async def get_ticket_detail(
    ticket_id: str,
    admin: dict = Depends(verify_token)
):
    """Récupère les détails d'un ticket avec messages"""
    # Récupérer le ticket
    # Récupérer les messages
    return {"ticket_id": ticket_id}

@app.post("/api/tickets/{ticket_id}/reply")
async def reply_to_ticket(
    ticket_id: str,
    reply: TicketReply,
    admin: dict = Depends(verify_token)
):
    """Ajoute une réponse à un ticket"""
    admin_id = admin.get('user_id')
    
    # Ajouter le message
    # Mettre à jour le statut
    return {"success": True, "message_id": "msg_123"}

@app.patch("/api/tickets/{ticket_id}")
async def update_ticket(
    ticket_id: str,
    update: TicketUpdate,
    admin: dict = Depends(verify_token)
):
    """Met à jour un ticket (statut, priorité, assignation)"""
    # Mettre à jour en DB
    return {"success": True}

@app.post("/api/tickets/{ticket_id}/close")
async def close_ticket(
    ticket_id: str,
    reason: Optional[str] = "",
    admin: dict = Depends(verify_token)
):
    """Ferme un ticket"""
    admin_id = admin.get('user_id')
    # Fermer le ticket
    return {"success": True}

@app.get("/api/tickets/stats/overview")
async def get_ticket_stats(admin: dict = Depends(verify_token)):
    """Statistiques globales des tickets"""
    return {
        "total": 0,
        "open": 0,
        "in_progress": 0,
        "resolved": 0,
        "avg_resolution_hours": 0
    }

@app.get("/api/tickets/stats/agent/{agent_id}")
async def get_agent_stats(agent_id: int, admin: dict = Depends(verify_token)):
    """Statistiques d'un agent spécifique"""
    return {
        "agent_id": agent_id,
        "tickets_assigned": 0,
        "tickets_resolved": 0,
        "avg_resolution_hours": 0
    }

# Webhook pour recevoir notifications de nouveaux tickets
@app.post("/webhook/tickets/new")
async def webhook_new_ticket(ticket_data: dict):
    """Webhook appelé quand un nouveau ticket est créé"""
    # Notifier les admins connectés via WebSocket
    return {"received": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
