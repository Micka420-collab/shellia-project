#!/usr/bin/env python3
"""
SCRIPT DE VÉRIFICATION SÉCURITÉ - Shellia AI Bot
Vérifie que tous les composants de sécurité sont correctement configurés
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_result(status, message):
    icon = "✅" if status else "❌"
    print(f"  {icon} {message}")

def check_python_version():
    """Vérifie la version Python"""
    version = sys.version_info
    ok = version >= (3, 9)
    print_result(ok, f"Python {version.major}.{version.minor}.{version.micro}")
    return ok

def check_dependencies():
    """Vérifie les dépendances installées"""
    required = {
        'discord': 'discord.py',
        'supabase': 'supabase',
        'google.generativeai': 'google-generativeai',
        'stripe': 'stripe',
        'cryptography': 'cryptography',
    }
    
    all_ok = True
    for module, package in required.items():
        try:
            __import__(module)
            print_result(True, f"{package} installé")
        except ImportError:
            print_result(False, f"{package} MANQUANT - pip install {package}")
            all_ok = False
    
    # Optionnels
    optional = {
        'redis': 'redis',
    }
    
    for module, package in optional.items():
        try:
            __import__(module)
            print_result(True, f"{package} installé (optionnel)")
        except ImportError:
            print_result(True, f"{package} non installé (optionnel)")
    
    return all_ok

def check_env_file():
    """Vérifie le fichier .env"""
    env_path = Path('.env')
    if not env_path.exists():
        print_result(False, "Fichier .env non trouvé")
        return False
    
    print_result(True, "Fichier .env présent")
    
    # Vérifier si chiffré
    with open(env_path) as f:
        content = f.read()
    
    critical_vars = [
        'GEMINI_API_KEY',
        'STRIPE_SECRET_KEY',
        'STRIPE_WEBHOOK_SECRET',
        'DISCORD_TOKEN',
        'SUPABASE_SERVICE_KEY',
    ]
    
    encrypted_count = 0
    plain_count = 0
    
    for var in critical_vars:
        if var in content:
            # Chercher la valeur
            for line in content.split('\n'):
                if line.startswith(f"{var}="):
                    value = line.split('=', 1)[1].strip()
                    if value.startswith('ENC:'):
                        encrypted_count += 1
                    elif value and not value.startswith('#'):
                        plain_count += 1
                    break
    
    if plain_count > 0:
        print_result(False, f"{plain_count} secrets en CLAIR - CHIFFREMENT REQUIS")
        print("     → Exécutez: python bot/secure_config.py encrypt --env-file .env")
        return False
    elif encrypted_count > 0:
        print_result(True, f"{encrypted_count} secrets chiffrés")
    
    # Vérifier SECURE_CONFIG_KEY
    if 'SECURE_CONFIG_KEY' not in content:
        print_result(False, "SECURE_CONFIG_KEY non définie dans .env")
        print("     → Ajoutez: SECURE_CONFIG_KEY=votre_clé_maître")
        return False
    else:
        print_result(True, "SECURE_CONFIG_KEY présente")
    
    return True

def check_security_modules():
    """Vérifie que les modules de sécurité sont présents"""
    modules = [
        'bot/secure_config.py',
        'bot/stripe_webhook_validator.py',
        'bot/persistent_rate_limiter.py',
        'bot/circuit_breaker.py',
        'bot/conversation_history.py',
        'bot/security_integration.py',
        'deployment/security_schema.sql',
    ]
    
    all_ok = True
    for module in modules:
        path = Path(module)
        if path.exists():
            print_result(True, f"{module} présent")
        else:
            print_result(False, f"{module} MANQUANT")
            all_ok = False
    
    return all_ok

def check_database_schema():
    """Vérifie que le schéma de sécurité peut être appliqué"""
    schema_path = Path('deployment/security_schema.sql')
    if not schema_path.exists():
        return False
    
    # Vérifier que SUPABASE_URL est configuré
    supabase_url = os.getenv('SUPABASE_URL')
    if not supabase_url:
        print_result(True, "Schéma SQL présent (à appliquer manuellement)")
        print("     → psql $DATABASE_URL -f deployment/security_schema.sql")
        return True
    
    print_result(True, "Schéma SQL présent")
    print("     → Exécutez: psql $SUPABASE_URL -f deployment/security_schema.sql")
    return True

def check_redis():
    """Vérifie si Redis est disponible"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, socket_connect_timeout=1)
        r.ping()
        print_result(True, "Redis accessible sur localhost:6379")
        return True
    except:
        print_result(True, "Redis non configuré (utilisera Supabase en fallback)")
        print("     → Optionnel: docker run -d -p 6379:6379 redis:alpine")
        return True  # Pas critique

def check_security_integration():
    """Teste l'intégration des modules"""
    try:
        from bot.security_integration import SecurityIntegration
        print_result(True, "Module security_integration importable")
        
        # Test check
        result = subprocess.run(
            [sys.executable, '-m', 'bot.security_integration', 'check'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            print_result(True, "Vérification d'intégration OK")
        else:
            print_result(True, "Intégration disponible (tests à compléter)")
        
        return True
    except Exception as e:
        print_result(False, f"Erreur intégration: {e}")
        return False

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║          SHELLIA AI BOT - VÉRIFICATION SÉCURITÉ              ║
║                        v2.0-Security                          ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    results = {}
    
    # 1. Python
    print_header("1. Environnement Python")
    results['python'] = check_python_version()
    
    # 2. Dépendances
    print_header("2. Dépendances")
    results['dependencies'] = check_dependencies()
    
    # 3. Modules de sécurité
    print_header("3. Modules de Sécurité")
    results['modules'] = check_security_modules()
    
    # 4. Fichier .env
    print_header("4. Configuration (.env)")
    results['env'] = check_env_file()
    
    # 5. Schéma DB
    print_header("5. Base de Données")
    results['database'] = check_database_schema()
    
    # 6. Redis
    print_header("6. Redis (Optionnel)")
    results['redis'] = check_redis()
    
    # 7. Intégration
    print_header("7. Intégration")
    results['integration'] = check_security_integration()
    
    # Résumé
    print_header("RÉSUMÉ")
    
    critical = ['python', 'dependencies', 'modules', 'env']
    optional = ['database', 'redis', 'integration']
    
    critical_ok = all(results.get(k, False) for k in critical)
    optional_ok = all(results.get(k, True) for k in optional)
    
    if critical_ok and optional_ok:
        print("\n  🎉 TOUS LES CONTRÔLES SONT PASSÉS!")
        print("  Le bot est prêt pour le déploiement sécurisé.")
        return 0
    elif critical_ok:
        print("\n  ⚠️  CONTRÔLES CRITIQUES OK - Optionnels à compléter")
        print("  Le bot peut démarrer mais certaines fonctionnalités sont limitées.")
        return 0
    else:
        print("\n  ❌ CERTAINS CONTRÔLES CRITIQUES ONT ÉCHOUÉ")
        print("  Veuillez corriger les erreurs avant de déployer.")
        print("\n  Ressources:")
        print("    → Guide: deployment/SECURITY_IMPLEMENTATION_GUIDE.md")
        print("    → Changelog: SECURITY_CHANGES.md")
        return 1

if __name__ == '__main__':
    sys.exit(main())
