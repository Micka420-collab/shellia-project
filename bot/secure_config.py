"""
CONFIGURATION SÉCURISÉE - Shellia AI Bot
Gestion des secrets avec chiffrement Fernet + Vault optionnel
"""

import os
import json
import base64
import hashlib
import secrets
from typing import Optional, Dict, Any
from dataclasses import dataclass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import warnings


class SecureConfigError(Exception):
    """Erreur de configuration sécurisée"""
    pass


class SecureConfigManager:
    """
    Gestionnaire de configuration sécurisée
    Chiffre les secrets avec Fernet (AES-128-CBC + HMAC)
    """
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Args:
            master_key: Clé maître (32 bytes base64). Si None, utilise SECURE_CONFIG_KEY env var
        """
        self.master_key = master_key or os.getenv('SECURE_CONFIG_KEY')
        self._cache: Dict[str, Any] = {}
        self._fernet: Optional[Fernet] = None
        
        if self.master_key:
            self._init_fernet()
    
    def _init_fernet(self):
        """Initialise Fernet avec la clé maître"""
        try:
            # Si la clé est brute (pas base64), la dériver
            if len(self.master_key) < 32:
                # Dériver une clé Fernet à partir d'un mot de passe
                key = self._derive_key(self.master_key)
            else:
                # Clé déjà en base64
                key = self.master_key.encode() if isinstance(self.master_key, str) else self.master_key
            
            self._fernet = Fernet(key)
        except Exception as e:
            warnings.warn(f"Impossible d'initialiser le chiffrement: {e}")
            self._fernet = None
    
    def _derive_key(self, password: str, salt: Optional[bytes] = None) -> bytes:
        """Dérive une clé Fernet à partir d'un mot de passe"""
        if salt is None:
            # Utiliser un salt fixe (à changer en production)
            salt = os.getenv('SECURE_CONFIG_SALT', 'shellia-salt-2026').encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt(self, plaintext: str) -> str:
        """
        Chiffre une valeur
        
        Returns:
            String base64 du ciphertext
        """
        if not self._fernet:
            raise SecureConfigError("Fernet non initialisé - impossible de chiffrer")
        
        encrypted = self._fernet.encrypt(plaintext.encode('utf-8'))
        return encrypted.decode('utf-8')
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Déchiffre une valeur
        
        Args:
            ciphertext: String base64 du ciphertext
        """
        if not self._fernet:
            raise SecureConfigError("Fernet non initialisé - impossible de déchiffrer")
        
        decrypted = self._fernet.decrypt(ciphertext.encode('utf-8'))
        return decrypted.decode('utf-8')
    
    def get_secret(self, key: str, encrypted: bool = False) -> Optional[str]:
        """
        Récupère un secret
        
        Args:
            key: Nom de la variable d'environnement
            encrypted: Si True, déchiffre la valeur
        """
        # Cache
        if key in self._cache:
            return self._cache[key]
        
        # Récupérer depuis l'environnement
        value = os.getenv(key)
        if not value:
            return None
        
        # Déchiffrer si nécessaire
        if encrypted and value.startswith('ENC:'):
            ciphertext = value[4:]  # Enlever le prefix ENC:
            value = self.decrypt(ciphertext)
        
        # Mettre en cache
        self._cache[key] = value
        return value
    
    def rotate_key(self, new_master_key: str, env_file: str = '.env') -> Dict[str, str]:
        """
        Effectue une rotation de clé
        
        1. Déchiffre tous les secrets avec l'ancienne clé
        2. Les rechiffre avec la nouvelle clé
        3. Retourne les nouvelles valeurs à mettre à jour
        
        Returns:
            Dict des secrets rechiffrés
        """
        if not self._fernet:
            raise SecureConfigError("Ancienne clé non initialisée")
        
        # Sauvegarder l'ancienne clé
        old_fernet = self._fernet
        
        # Initialiser avec la nouvelle clé
        self.master_key = new_master_key
        self._init_fernet()
        
        if not self._fernet:
            self._fernet = old_fernet
            raise SecureConfigError("Nouvelle clé invalide")
        
        # Liste des clés à rotater
        keys_to_rotate = [
            'GEMINI_API_KEY',
            'STRIPE_SECRET_KEY',
            'STRIPE_WEBHOOK_SECRET',
            'DISCORD_TOKEN',
            'SUPABASE_SERVICE_KEY',
        ]
        
        rotated = {}
        
        for key in keys_to_rotate:
            value = os.getenv(key)
            if value and value.startswith('ENC:'):
                try:
                    # Déchiffrer avec ancienne clé
                    old_ciphertext = value[4:]
                    plaintext = old_fernet.decrypt(old_ciphertext.encode()).decode()
                    
                    # Rechiffrer avec nouvelle clé
                    new_ciphertext = self._fernet.encrypt(plaintext.encode()).decode()
                    rotated[key] = f"ENC:{new_ciphertext}"
                except Exception as e:
                    print(f"Échec rotation {key}: {e}")
        
        # Restaurer l'ancienne clé pour continuer à fonctionner
        self._fernet = old_fernet
        self.master_key = os.getenv('SECURE_CONFIG_KEY')
        
        return rotated
    
    @staticmethod
    def generate_master_key() -> str:
        """Génère une nouvelle clé maître sécurisée"""
        return Fernet.generate_key().decode('utf-8')
    
    @staticmethod
    def encrypt_env_file(master_key: str, env_file: str = '.env') -> str:
        """
        Chiffre les valeurs sensibles dans un fichier .env
        
        Returns:
            Chemin du fichier chiffré créé
        """
        manager = SecureConfigManager(master_key)
        
        sensitive_keys = [
            'GEMINI_API_KEY',
            'STRIPE_SECRET_KEY',
            'STRIPE_WEBHOOK_SECRET',
            'DISCORD_TOKEN',
            'SUPABASE_SERVICE_KEY',
        ]
        
        output_lines = []
        
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    output_lines.append(line)
                    continue
                
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    
                    if key in sensitive_keys and value and not value.startswith('ENC:'):
                        encrypted = manager.encrypt(value)
                        output_lines.append(f"{key}=ENC:{encrypted}")
                    else:
                        output_lines.append(line)
                else:
                    output_lines.append(line)
        
        # Écrire le fichier chiffré
        encrypted_file = f"{env_file}.encrypted"
        with open(encrypted_file, 'w') as f:
            f.write('\n'.join(output_lines))
        
        return encrypted_file


class HashiCorpVaultClient:
    """
    Client HashiCorp Vault pour la gestion avancée des secrets
    (Optionnel - nécessite le package hvac)
    """
    
    def __init__(
        self,
        vault_url: str,
        role_id: Optional[str] = None,
        secret_id: Optional[str] = None,
        token: Optional[str] = None
    ):
        try:
            import hvac
        except ImportError:
            raise SecureConfigError("Package 'hvac' requis: pip install hvac")
        
        self.client = hvac.Client(url=vault_url)
        
        if token:
            self.client.token = token
        elif role_id and secret_id:
            # AppRole authentication
            self.client.auth.approle.login(
                role_id=role_id,
                secret_id=secret_id
            )
        
        if not self.client.is_authenticated():
            raise SecureConfigError("Échec authentification Vault")
    
    def get_secret(self, path: str, key: Optional[str] = None) -> Optional[str]:
        """
        Récupère un secret depuis Vault
        
        Args:
            path: Chemin du secret (ex: 'secret/data/shellia')
            key: Clé spécifique dans le secret
        """
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point='secret'
            )
            
            data = response['data']['data']
            
            if key:
                return data.get(key)
            return json.dumps(data)
            
        except Exception as e:
            print(f"Erreur Vault: {e}")
            return None
    
    def put_secret(self, path: str, data: Dict[str, str]):
        """Crée ou met à jour un secret"""
        self.client.secrets.kv.v2.create_or_update_secret(
            path=path,
            secret=data,
            mount_point='secret'
        )


# ============ UTILISATION ============
"""
# 1. Générer une clé maître (faire UNE SEULE FOIS)
from secure_config import SecureConfigManager

master_key = SecureConfigManager.generate_master_key()
print(f"CLÉ MAÎTRE (à garder SECRÈTE): {master_key}")

# 2. Chiffrer le fichier .env
encrypted_file = SecureConfigManager.encrypt_env_file(master_key)
print(f"Fichier chiffré: {encrypted_file}")

# 3. Remplacer .env par .env.encrypted et définir SECURE_CONFIG_KEY
# mv .env.encrypted .env
# export SECURE_CONFIG_KEY="votre_clé_maître"

# 4. Dans le code
from secure_config import SecureConfigManager

config = SecureConfigManager()  # Utilise SECURE_CONFIG_KEY

gemini_key = config.get_secret('GEMINI_API_KEY', encrypted=True)
stripe_key = config.get_secret('STRIPE_SECRET_KEY', encrypted=True)
"""


# ============ CLASSE CONFIG PRINCIPALE ============

@dataclass
class ShelliaConfig:
    """Configuration centralisée de Shellia AI"""
    
    # Discord
    discord_token: str = ""
    discord_application_id: str = ""
    
    # Supabase
    supabase_url: str = ""
    supabase_service_key: str = ""
    
    # Gemini
    gemini_api_key: str = ""
    
    # Stripe
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    
    # Security
    secure_config_key: str = ""
    
    @classmethod
    def from_env(cls, encrypted: bool = False) -> 'ShelliaConfig':
        """Charge la configuration depuis les variables d'environnement"""
        
        config_manager = None
        if encrypted or os.getenv('SECURE_CONFIG_KEY'):
            config_manager = SecureConfigManager()
        
        def get(key: str) -> str:
            if config_manager:
                return config_manager.get_secret(key, encrypted=encrypted) or ""
            return os.getenv(key, "")
        
        return cls(
            discord_token=get('DISCORD_TOKEN'),
            discord_application_id=get('DISCORD_APPLICATION_ID'),
            supabase_url=get('SUPABASE_URL'),
            supabase_service_key=get('SUPABASE_SERVICE_KEY'),
            gemini_api_key=get('GEMINI_API_KEY'),
            stripe_secret_key=get('STRIPE_SECRET_KEY'),
            stripe_publishable_key=get('STRIPE_PUBLISHABLE_KEY'),
            stripe_webhook_secret=get('STRIPE_WEBHOOK_SECRET'),
            secure_config_key=get('SECURE_CONFIG_KEY'),
        )
    
    def validate(self) -> list:
        """Valide que tous les secrets requis sont présents"""
        required = [
            ('discord_token', 'DISCORD_TOKEN'),
            ('supabase_url', 'SUPABASE_URL'),
            ('supabase_service_key', 'SUPABASE_SERVICE_KEY'),
            ('gemini_api_key', 'GEMINI_API_KEY'),
            ('stripe_secret_key', 'STRIPE_SECRET_KEY'),
        ]
        
        missing = []
        for attr, env_name in required:
            if not getattr(self, attr):
                missing.append(env_name)
        
        return missing


# Utilitaire CLI pour le chiffrement
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Shellia Secure Config')
    parser.add_argument('command', choices=['generate-key', 'encrypt', 'rotate', 'verify'])
    parser.add_argument('--env-file', default='.env', help='Fichier .env')
    parser.add_argument('--key', help='Clé maître (ou utiliser SECURE_CONFIG_KEY)')
    
    args = parser.parse_args()
    
    if args.command == 'generate-key':
        key = SecureConfigManager.generate_master_key()
        print(f"Nouvelle clé maître: {key}")
        print("⚠️  CONSERVEZ CETTE CLÉ DANS UN ENDROIT SÛR!")
        
    elif args.command == 'encrypt':
        key = args.key or os.getenv('SECURE_CONFIG_KEY')
        if not key:
            print("Erreur: --key ou SECURE_CONFIG_KEY requis")
            exit(1)
        
        output = SecureConfigManager.encrypt_env_file(key, args.env_file)
        print(f"Fichier chiffré créé: {output}")
        print(f"Remplacez {args.env_file} par {output}")
        
    elif args.command == 'verify':
        key = args.key or os.getenv('SECURE_CONFIG_KEY')
        if not key:
            print("Erreur: --key ou SECURE_CONFIG_KEY requis")
            exit(1)
        
        config = ShelliaConfig.from_env(encrypted=True)
        missing = config.validate()
        
        if missing:
            print(f"❌ Secrets manquants: {', '.join(missing)}")
        else:
            print("✅ Tous les secrets sont présents et chiffrés")
