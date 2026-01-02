"""
Test específico para el ejercicio de Tabla de Multiplicar

FIX Cortez36: Now uses shared sandbox utility from backend.utils.sandbox
"""
import re

# FIX Cortez36: Import from shared utility module (consolidated from duplicate code)
from backend.utils.sandbox import execute_python_code


def test_tabla_multiplicar():
    """Test del ejercicio SEC-06: Tabla de Multiplicar"""
    
    # Código original (con líneas vacías)
    codigo_original = '''numero = int(input("Ingrese un número entero: "))

print(f"""
{numero} x 0 = {numero * 0}
{numero} x 1 = {numero * 1}
{numero} x 2 = {numero * 2}
{numero} x 3 = {numero * 3}
{numero} x 4 = {numero * 4}
{numero} x 5 = {numero * 5}
{numero} x 6 = {numero * 6}
{numero} x 7 = {numero * 7}
{numero} x 8 = {numero * 8}
{numero} x 9 = {numero * 9}
""")'''

    # Código alternativo (sin líneas vacías)
    codigo_alternativo = '''numero = int(input("Ingrese un número entero: "))

print(f"""{numero} x 0 = {numero * 0}
{numero} x 1 = {numero * 1}
{numero} x 2 = {numero * 2}
{numero} x 3 = {numero * 3}
{numero} x 4 = {numero * 4}
{numero} x 5 = {numero * 5}
{numero} x 6 = {numero * 6}
{numero} x 7 = {numero * 7}
{numero} x 8 = {numero * 8}
{numero} x 9 = {numero * 9}""")'''

    tests = [
        {
            "nombre": "Test 1: Tabla del 5",
            "input": "5\n",
            "expected_pattern": ".*5 x 0 = 0.*5 x 1 = 5.*5 x 9 = 45.*"
        },
        {
            "nombre": "Test 2: Tabla del 3",
            "input": "3\n",
            "expected_pattern": ".*3 x 0 = 0.*3 x 5 = 15.*3 x 9 = 27.*"
        }
    ]
    
    print("\n" + "="*70)
    print("Probando ejercicio: Tabla de Multiplicar (SEC-06)")
    print("="*70)
    
    for version_name, codigo in [("ORIGINAL (con líneas vacías)", codigo_original), 
                                   ("ALTERNATIVO (sin líneas vacías)", codigo_alternativo)]:
        print(f"\n{'='*70}")
        print(f"Versión: {version_name}")
        print(f"{'='*70}")
        print(f"\nCódigo:")
        print("-" * 40)
        print(codigo)
        print("-" * 40)
        
        tests_passed = 0
        for test in tests:
            print(f"\n{test['nombre']}")
            print(f"  Input: {test['input'].strip()}")
            
            stdout, stderr, exec_time = execute_python_code(
                codigo,
                test['input'],
                timeout_seconds=5
            )
            
            if stderr:
                print(f"  ❌ ERROR: {stderr}")
            else:
                print(f"  Output:")
                print("  " + "\n  ".join(stdout.split("\n")))
                print(f"\n  Expected pattern: {test['expected_pattern']}")
                
                # Probar el pattern
                if re.search(test['expected_pattern'], stdout, re.DOTALL):
                    print(f"  ✅ PASADO (tiempo: {exec_time}ms)")
                    tests_passed += 1
                else:
                    print(f"  ❌ FALLÓ - Pattern no coincide")
                    # Mostrar qué partes del pattern no coinciden
                    patterns = test['expected_pattern'].replace(".*", "|").split("|")
                    patterns = [p.strip() for p in patterns if p.strip()]
                    print(f"  Buscando partes:")
                    for p in patterns:
                        if p in stdout:
                            print(f"    ✅ Encontrado: '{p}'")
                        else:
                            print(f"    ❌ No encontrado: '{p}'")
        
        print(f"\n{'-'*70}")
        print(f"Resultado: {tests_passed}/{len(tests)} tests pasados")
        print(f"{'-'*70}")


if __name__ == "__main__":
    test_tabla_multiplicar()
