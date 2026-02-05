"""
🔌 MAXIS API - Interface de contrôle pour Shellia
Reçoit et exécute les commandes de Shellia Controller
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn
import asyncio
from datetime import datetime

app = FastAPI(title="Maxis Control API", version="2.1")

# Sécurité
API_KEY = "changeme-in-production"
api_key_header = APIKeyHeader(name="X-API-Key")

def verify_api_key(api_key: str = Header(...)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

# Modèles de données
class ConfigUpdate(BaseModel):
    key: str
    value: str

class PromoCommand(BaseModel):
    discount: int
    target: str
    duration_hours: int
    created_by: int

class GiveawayCommand(BaseModel):
    milestone: int
    created_by: int

class ExecuteCommand(BaseModel):
    command: str
    executed_by: int

# État de Maxis
maxis_state = {
    'online': True,
    'version': '2.1-PLUS',
    'uptime': datetime.utcnow(),
    'last_command': None
}

# Référence au bot Maxis (sera injectée)
maxis_bot_instance = None

def set_maxis_bot(bot_instance):
    """Définit l'instance du bot Maxis"""
    global maxis_bot_instance
    maxis_bot_instance = bot_instance

# ============ ENDPOINTS DE SANTÉ ============

@app.get("/health")
async def health_check():
    """Vérifie si Maxis est en ligne"""
    return {
        "status": "online",
        "version": maxis_state['version'],
        "uptime": (datetime.utcnow() - maxis_state['uptime']).total_seconds()
    }

# ============ ENDPOINTS DE STATS ============

@app.get("/stats")
async def get_stats(api_key: str = Depends(verify_api_key)):
    """Récupère les statistiques de Maxis"""
    if not maxis_bot_instance:
        raise HTTPException(status_code=503, detail="Maxis not initialized")
    
    # Récupérer les stats depuis le bot
    stats = await maxis_bot_instance.get_stats() if hasattr(maxis_bot_instance, 'get_stats') else {}
    
    return {
        "members": stats.get('members', 0),
        "revenue": stats.get('revenue', 0),
        "orders": stats.get('orders', 0),
        "conversion": stats.get('conversion', 0),
        "giveaways": stats.get('giveaways', 0),
        "promotions": stats.get('promotions', 0),
        "timestamp": datetime.utcnow().isoformat()
    }

# ============ ENDPOINTS DE CONTRÔLE ============

@app.post("/control/restart")
async def restart_maxis(api_key: str = Depends(verify_api_key)):
    """Redémarre Maxis"""
    maxis_state['online'] = False
    # Logique de redémarrage ici
    return {"success": True, "message": "Maxis restart initiated"}

@app.post("/control/config")
async def update_config(config: ConfigUpdate, api_key: str = Depends(verify_api_key)):
    """Met à jour la configuration"""
    if maxis_bot_instance and hasattr(maxis_bot_instance, 'update_config'):
        await maxis_bot_instance.update_config(config.key, config.value)
    
    return {"success": True, "key": config.key, "value": config.value}

@app.post("/control/execute")
async def execute_command(cmd: ExecuteCommand, api_key: str = Depends(verify_api_key)):
    """Exécute une commande sur Maxis"""
    maxis_state['last_command'] = {
        'command': cmd.command,
        'by': cmd.executed_by,
        'at': datetime.utcnow().isoformat()
    }
    
    # Exécuter la commande
    if maxis_bot_instance and hasattr(maxis_bot_instance, 'execute_command'):
        output = await maxis_bot_instance.execute_command(cmd.command)
        return {"success": True, "output": output}
    
    return {"success": False, "error": "Command execution not available"}

@app.get("/control/report")
async def get_report(api_key: str = Depends(verify_api_key)):
    """Génère un rapport complet"""
    report = {
        "system_status": "online",
        "version": maxis_state['version'],
        "uptime_hours": (datetime.utcnow() - maxis_state['uptime']).total_seconds() / 3600,
        "last_command": maxis_state['last_command']
    }
    
    if maxis_bot_instance and hasattr(maxis_bot_instance, 'get_detailed_report'):
        report.update(await maxis_bot_instance.get_detailed_report())
    
    return {"success": True, "report": report}

# ============ ENDPOINTS MARKETING ============

@app.post("/marketing/promo")
async def create_promotion(promo: PromoCommand, api_key: str = Depends(verify_api_key)):
    """Crée une promotion"""
    if maxis_bot_instance and hasattr(maxis_bot_instance, 'create_promotion'):
        code = await maxis_bot_instance.create_promotion(
            promo.discount,
            promo.target,
            promo.duration_hours
        )
        return {"success": True, "code": code}
    
    return {"success": False, "error": "Promotion creation not available"}

@app.post("/marketing/giveaway")
async def create_giveaway(giveaway: GiveawayCommand, api_key: str = Depends(verify_api_key)):
    """Crée un giveaway"""
    if maxis_bot_instance and hasattr(maxis_bot_instance, 'create_giveaway'):
        giveaway_id = await maxis_bot_instance.create_giveaway(
            giveaway.milestone
        )
        return {"success": True, "giveaway_id": giveaway_id}
    
    return {"success": False, "error": "Giveaway creation not available"}

# ============ LANCEMENT ============

def start_api_server(bot_instance, api_key: str, host: str = "0.0.0.0", port: int = 8080):
    """Démarre le serveur API"""
    global API_KEY, maxis_bot_instance
    API_KEY = api_key
    maxis_bot_instance = bot_instance
    
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
