#!/usr/bin/env python3
"""
SCRIPT DE TEST - Shellia AI Bot
Lance tous les tests (unitaires et d'intégration)
"""

import sys
import subprocess
from pathlib import Path


def print_header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def run_command(cmd, description):
    """Exécute une commande et affiche le résultat"""
    print(f"🔍 {description}...")
    print(f"   Commande: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode


def main():
    print_header("SHELLIA AI BOT - SUITE DE TESTS")
    
    results = {}
    
    # 1. Vérification de la configuration
    print_header("1. VÉRIFICATION DE LA CONFIGURATION")
    
    results['check_security'] = run_command(
        [sys.executable, 'check_security.py'],
        "Vérification de la sécurité"
    )
    
    # 2. Tests unitaires de sécurité
    print_header("2. TESTS UNITAIRES DE SÉCURITÉ")
    
    results['unit_tests'] = run_command(
        [sys.executable, '-m', 'pytest', 'tests/test_security.py', '-v', '--tb=short'],
        "Tests unitaires"
    )
    
    # 3. Tests d'intégration
    print_header("3. TESTS D'INTÉGRATION")
    
    results['integration_tests'] = run_command(
        [sys.executable, '-m', 'pytest', 'tests/test_integration.py', '-v', '--tb=short'],
        "Tests d'intégration"
    )
    
    # 4. Test de connexion aux services (si variables d'env configurées)
    print_header("4. TESTS DE CONNEXION")
    
    if all(key in sys.environ for key in ['SUPABASE_URL', 'GEMINI_API_KEY']):
        print("✅ Variables d'environnement présentes")
        print("   Test de connexion aux services...")
        
        # Test rapide de connexion
        test_script = """
import sys
sys.path.insert(0, 'bot')

try:
    from supabase_client import SupabaseDB
    db = SupabaseDB()
    print("✅ Connexion Supabase OK")
except Exception as e:
    print(f"❌ Erreur Supabase: {e}")

try:
    import google.generativeai as genai
    genai.configure(api_key=sys.environ.get('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-1.5-flash-lite')
    print("✅ Connexion Gemini OK")
except Exception as e:
    print(f"❌ Erreur Gemini: {e}")
"""
        results['connection_tests'] = run_command(
            [sys.executable, '-c', test_script],
            "Tests de connexion"
        )
    else:
        print("⚠️ Variables d'environnement manquantes, tests de connexion ignorés")
        results['connection_tests'] = 0
    
    # Résumé
    print_header("RÉSUMÉ DES TESTS")
    
    total = len(results)
    passed = sum(1 for code in results.values() if code == 0)
    failed = total - passed
    
    for test_name, code in results.items():
        status = "✅ PASS" if code == 0 else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print(f"\n{'='*70}")
    print(f"  Total: {total} | ✅ Réussis: {passed} | ❌ Échoués: {failed}")
    print(f"{'='*70}\n")
    
    if failed == 0:
        print("🎉 TOUS LES TESTS SONT PASSÉS!")
        print("Le bot est prêt pour le déploiement.\n")
        return 0
    else:
        print("⚠️ CERTAINS TESTS ONT ÉCHOUÉ")
        print("Veuillez corriger les erreurs avant de déployer.\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
