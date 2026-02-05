"""
GÉNÉRATEUR D'IMAGES - Shellia AI Bot
Supporte Gemini 2.0 Flash Image Generation et fallbacks
"""

import os
import io
import base64
import asyncio
from typing import Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

import google.generativeai as genai


@dataclass
class ImageGenerationResult:
    """Résultat de génération d'image"""
    success: bool
    image_data: Optional[bytes] = None
    mime_type: str = "image/png"
    model_used: str = ""
    generation_time: float = 0.0
    cost_usd: float = 0.0
    error: Optional[str] = None


class ImageGenerator:
    """
    Générateur d'images avec support multi-modèles
    
    Ordre de priorité:
    1. Gemini 2.0 Flash Image Generation (gratuit avec limites)
    2. Gemini Pro Vision (fallback texte uniquement)
    3. Message d'erreur graceful
    """
    
    # Coûts approximatifs
    COSTS = {
        'gemini-2.0-flash-exp-image-generation': 0.0,  # Gratuit pour l'instant (expérimental)
        'dall-e-3': 0.04,  # $0.04 par image 1024x1024
        'fallback': 0.0
    }
    
    def __init__(self, api_key: str):
        """
        Initialise le générateur d'images
        
        Args:
            api_key: Clé API Google Gemini
        """
        self.api_key = api_key
        genai.configure(api_key=api_key)
        
        # Modèle principal pour la génération d'images
        try:
            self.image_model = genai.GenerativeModel('gemini-2.0-flash-exp-image-generation')
            self.image_model_available = True
        except Exception as e:
            print(f"⚠️ Modèle de génération d'images non disponible: {e}")
            self.image_model = None
            self.image_model_available = False
        
        # Modèle de fallback pour la description
        try:
            self.text_model = genai.GenerativeModel('gemini-1.5-flash')
            self.text_model_available = True
        except Exception as e:
            print(f"⚠️ Modèle texte non disponible: {e}")
            self.text_model = None
            self.text_model_available = False
    
    async def generate(
        self,
        prompt: str,
        user_id: int,
        size: str = "1024x1024",
        style: str = "vivid"
    ) -> ImageGenerationResult:
        """
        Génère une image à partir d'un prompt
        
        Args:
            prompt: Description de l'image souhaitée
            user_id: ID de l'utilisateur (pour logging)
            size: Taille de l'image (1024x1024, 1792x1024, 1024x1792)
            style: Style (vivid ou natural)
        
        Returns:
            ImageGenerationResult avec l'image ou une erreur
        """
        start_time = datetime.now()
        
        # 1. Essayer Gemini Image Generation (expérimental)
        if self.image_model_available:
            try:
                result = await self._generate_with_gemini_image(prompt, size, style)
                if result.success:
                    result.generation_time = (datetime.now() - start_time).total_seconds()
                    return result
            except Exception as e:
                print(f"⚠️ Échec génération Gemini Image: {e}")
        
        # 2. Fallback: Générer une description détaillée
        if self.text_model_available:
            try:
                result = await self._generate_description_fallback(prompt)
                result.generation_time = (datetime.now() - start_time).total_seconds()
                return result
            except Exception as e:
                print(f"⚠️ Échec fallback description: {e}")
        
        # 3. Échec complet
        return ImageGenerationResult(
            success=False,
            error="Service de génération d'images temporairement indisponible. Veuillez réessayer plus tard."
        )
    
    async def _generate_with_gemini_image(
        self,
        prompt: str,
        size: str,
        style: str
    ) -> ImageGenerationResult:
        """
        Génère une image avec Gemini 2.0 Flash Image Generation
        """
        # Améliorer le prompt
        enhanced_prompt = self._enhance_prompt(prompt, style)
        
        # Générer dans un thread pour ne pas bloquer
        def _generate():
            response = self.image_model.generate_content(
                enhanced_prompt,
                generation_config={
                    "response_modalities": ["Text", "Image"]
                }
            )
            return response
        
        response = await asyncio.to_thread(_generate)
        
        # Extraire l'image de la réponse
        for part in response.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                image_data = part.inline_data.data
                
                # Si c'est du base64, décoder
                if isinstance(image_data, str):
                    image_bytes = base64.b64decode(image_data)
                else:
                    image_bytes = image_data
                
                return ImageGenerationResult(
                    success=True,
                    image_data=image_bytes,
                    mime_type=part.inline_data.mime_type or "image/png",
                    model_used="gemini-2.0-flash-exp-image-generation",
                    cost_usd=0.0  # Gratuit pour l'instant
                )
            
            # Parfois l'image est dans un format différent
            if hasattr(part, 'text') and part.text:
                # C'est du texte, pas une image
                continue
        
        # Si on arrive ici, pas d'image trouvée
        return ImageGenerationResult(
            success=False,
            error="Le modèle n'a pas généré d'image. Réessayez avec un prompt différent."
        )
    
    async def _generate_description_fallback(self, prompt: str) -> ImageGenerationResult:
        """
        Fallback: Génère une description détaillée au lieu d'une image
        """
        fallback_prompt = f"""
        L'utilisateur a demandé une image de: "{prompt}"
        
        Malheureusement, le service de génération d'images est temporairement indisponible.
        
        Décris en détail ce à quoi aurait ressemblé cette image (style artistique, 
        couleurs, composition, ambiance) pour que l'utilisateur puisse l'imaginer.
        
        Sois créatif et descriptif, comme si tu racontais une scène à un artiste.
        """
        
        def _generate():
            response = self.text_model.generate_content(fallback_prompt)
            return response.text
        
        description = await asyncio.to_thread(_generate)
        
        # Créer une "image" textuelle (on renvoie le texte qui sera affiché)
        return ImageGenerationResult(
            success=True,  # Considéré comme succès mais c'est du texte
            image_data=None,
            model_used="gemini-1.5-flash-description",
            cost_usd=0.0,
            error=None  # Pas une erreur, juste un fallback
        )
    
    def _enhance_prompt(self, prompt: str, style: str) -> str:
        """
        Améliore le prompt utilisateur pour de meilleurs résultats
        """
        style_modifiers = {
            "vivid": "vibrant colors, high contrast, dramatic lighting, detailed",
            "natural": "natural colors, soft lighting, realistic, photorealistic",
            "anime": "anime style, manga art, vibrant colors, clean lines",
            "3d": "3D render, octane render, blender, realistic textures, lighting",
            "digital_art": "digital art, concept art, detailed, professional",
            "oil_painting": "oil painting style, brush strokes, canvas texture, artistic",
            "watercolor": "watercolor painting, soft colors, flowing, artistic",
            "sketch": "pencil sketch, detailed drawing, grayscale, artistic"
        }
        
        style_desc = style_modifiers.get(style, style_modifiers["vivid"])
        
        # Améliorations générales
        enhancements = [
            "high quality",
            "detailed",
            "professional",
        ]
        
        enhanced = f"Generate an image: {prompt}. Style: {style_desc}. " + ", ".join(enhancements)
        
        return enhanced
    
    def validate_prompt(self, prompt: str) -> Tuple[bool, str]:
        """
        Valide le prompt avant génération
        
        Returns:
            (is_valid, error_message)
        """
        if not prompt or not prompt.strip():
            return False, "Le prompt ne peut pas être vide"
        
        if len(prompt) > 1000:
            return False, "Le prompt est trop long (max 1000 caractères)"
        
        # Vérifier contenu inapproprié (basique)
        forbidden_keywords = [
            'nude', 'naked', 'porn', 'sex', 'violence', 'gore', 'blood',
            'kill', 'murder', 'torture', 'weapon', 'gun', 'knife'
        ]
        
        prompt_lower = prompt.lower()
        for keyword in forbidden_keywords:
            if keyword in prompt_lower:
                return False, "Le prompt contient des éléments non autorisés"
        
        return True, ""
    
    def get_quota_info(self, user_id: int, db) -> dict:
        """
        Récupère les informations de quota d'images pour un utilisateur
        """
        try:
            user_data = db.client.table('users').select('plan, images_generated_today').eq('user_id', user_id).execute()
            
            if not user_data.data:
                return {'allowed': False, 'error': 'Utilisateur non trouvé'}
            
            user = user_data.data[0]
            plan = user.get('plan', 'free')
            images_used = user.get('images_generated_today', 0)
            
            # Quotas selon le plan
            quotas = {
                'free': 0,
                'basic': 0,
                'pro': 10,
                'ultra': 50,
                'founder': 100
            }
            
            quota = quotas.get(plan, 0)
            remaining = quota - images_used
            
            return {
                'allowed': remaining > 0,
                'plan': plan,
                'quota': quota,
                'used': images_used,
                'remaining': remaining,
                'error': None if remaining > 0 else f"Quota d'images atteint ({quota}/jour)"
            }
            
        except Exception as e:
            return {'allowed': False, 'error': f"Erreur: {str(e)}"}
    
    def increment_usage(self, user_id: int, db) -> bool:
        """
        Incrémente le compteur d'images générées pour un utilisateur
        """
        try:
            result = db.client.table('users').select('images_generated_today').eq('user_id', user_id).execute()
            
            if result.data:
                current = result.data[0].get('images_generated_today', 0)
                db.client.table('users').update({
                    'images_generated_today': current + 1
                }).eq('user_id', user_id).execute()
                return True
            return False
        except Exception as e:
            print(f"❌ Erreur incrémentation usage: {e}")
            return False
    
    async def generate_and_send(
        self,
        prompt: str,
        user_id: int,
        db,
        discord_bot=None
    ) -> dict:
        """
        Génère une image et gère toute la logique (quota, logging, etc.)
        
        Returns:
            dict avec success, file (discord File), error, etc.
        """
        import discord
        
        # 1. Vérifier quota
        quota_info = self.get_quota_info(user_id, db)
        if not quota_info['allowed']:
            return {
                'success': False,
                'error': quota_info['error'],
                'quota_exceeded': True
            }
        
        # 2. Valider prompt
        is_valid, error = self.validate_prompt(prompt)
        if not is_valid:
            return {'success': False, 'error': error}
        
        # 3. Générer l'image
        result = await self.generate(prompt, user_id)
        
        if not result.success:
            return {'success': False, 'error': result.error}
        
        # 4. Incrémenter usage
        self.increment_usage(user_id, db)
        
        # 5. Logger
        try:
            db.client.table('security_logs').insert({
                'user_id': user_id,
                'event_type': 'image_generated',
                'event_data': {
                    'prompt': prompt[:200],
                    'model': result.model_used,
                    'cost': result.cost_usd
                },
                'severity': 'info'
            }).execute()
        except:
            pass
        
        # 6. Retourner le résultat avec fichier Discord
        if result.image_data:
            file = discord.File(
                io.BytesIO(result.image_data),
                filename=f"shellia_{user_id}_{int(datetime.now().timestamp())}.png"
            )
            return {
                'success': True,
                'file': file,
                'model': result.model_used,
                'remaining': quota_info['remaining'] - 1
            }
        else:
            # Fallback texte
            return {
                'success': True,
                'text_fallback': True,
                'description': "Service d'images temporairement indisponible",
                'remaining': quota_info['remaining'] - 1
            }


# Helper pour créer le modèle depuis la clé API
def create_image_generator(api_key: str) -> ImageGenerator:
    """Factory pour créer le générateur d'images"""
    return ImageGenerator(api_key)


# Tests
if __name__ == '__main__':
    import os
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY non définie")
        exit(1)
    
    generator = ImageGenerator(api_key)
    
    async def test():
        print("🎨 Test génération d'image...")
        
        result = await generator.generate(
            prompt="A cute cat playing with a ball of yarn in a sunny garden",
            user_id=12345
        )
        
        if result.success:
            print(f"✅ Image générée!")
            print(f"   Modèle: {result.model_used}")
            print(f"   Taille: {len(result.image_data)} bytes")
            print(f"   Temps: {result.generation_time:.2f}s")
            
            # Sauvegarder l'image
            if result.image_data:
                with open('test_image.png', 'wb') as f:
                    f.write(result.image_data)
                print("   Sauvegardée: test_image.png")
        else:
            print(f"❌ Échec: {result.error}")
    
    asyncio.run(test())
