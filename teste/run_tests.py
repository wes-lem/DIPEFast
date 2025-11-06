#!/usr/bin/env python
"""
Script auxiliar para executar testes.
Facilita a execução dos testes com diferentes opções.
"""
import sys
import subprocess

def run_tests():
    """Executa todos os testes."""
    print("🧪 Executando todos os testes...\n")
    result = subprocess.run(
        ["pytest", "teste/", "-v", "--tb=short"],
        cwd="."
    )
    return result.returncode

def run_tests_fast():
    """Executa testes rapidamente (sem verbose)."""
    print("⚡ Executando testes (modo rápido)...\n")
    result = subprocess.run(
        ["pytest", "teste/", "--tb=line"],
        cwd="."
    )
    return result.returncode

def run_tests_coverage():
    """Executa testes com relatório de cobertura."""
    print("📊 Executando testes com cobertura...\n")
    result = subprocess.run(
        ["pytest", "teste/", "--cov=.", "--cov-report=html", "--cov-report=term"],
        cwd="."
    )
    return result.returncode

def run_specific_test(file_path):
    """Executa um arquivo de teste específico."""
    print(f"🎯 Executando teste: {file_path}\n")
    result = subprocess.run(
        ["pytest", f"teste/{file_path}", "-v"],
        cwd="."
    )
    return result.returncode

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--fast":
            sys.exit(run_tests_fast())
        elif sys.argv[1] == "--coverage":
            sys.exit(run_tests_coverage())
        elif sys.argv[1] == "--file" and len(sys.argv) > 2:
            sys.exit(run_specific_test(sys.argv[2]))
        else:
            print(f"Opção inválida: {sys.argv[1]}")
            print("\nUso:")
            print("  python teste/run_tests.py           # Executa todos os testes")
            print("  python teste/run_tests.py --fast      # Modo rápido")
            print("  python teste/run_tests.py --coverage  # Com cobertura")
            print("  python teste/run_tests.py --file test_routes.py  # Arquivo específico")
            sys.exit(1)
    else:
        sys.exit(run_tests())

