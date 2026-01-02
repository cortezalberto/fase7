"""
Test para verificar que el ejercicio de temperaturas ahora funciona

FIX Cortez36: Now uses shared sandbox utility from backend.utils.sandbox
"""
import re

# FIX Cortez36: Import from shared utility module (consolidated from duplicate code)
from backend.utils.sandbox import execute_python_code


# Código del usuario (correcto)
codigo_usuario = '''# NO TOCAR ESTAS LÍNEAS
# Ejercicio: Análisis de Temperaturas
temperaturas = [23.5, 25.1, 22.8, 24.3, 26.0, 23.9, 25.5]

# TODO: Calcula el promedio
total_temp = 0
for temp in temperaturas:
    total_temp += temp

promedio = total_temp / len(temperaturas)

# TODO: Encuentra máxima y mínima
temp_max = temperaturas[0]
temp_min = temperaturas[0]

for temp in temperaturas:
    if temp > temp_max:
        temp_max = temp
    if temp < temp_min:
        temp_min = temp

# TODO: Cuenta días sobre el promedio
dias_sobre_promedio = 0
for temp in temperaturas:
    if temp > promedio:
        dias_sobre_promedio += 1

# TODO: Imprime el reporte
print("=== REPORTE METEOROLÓGICO ===")
print(f"Promedio: {promedio:.2f}°C")
print(f"Máxima: {temp_max}°C")
print(f"Mínima: {temp_min}°C")
print(f"Días sobre promedio: {dias_sobre_promedio}")
'''

print("\n" + "="*70)
print("TEST CORREGIDO: Análisis de Temperaturas")
print("="*70)

# Test CORREGIDO del JSON
test_corregido = {
    "input": "",
    "expected": ".*Promedio:\\s*24\\.4[34]°C.*Máxima:\\s*26\\.0°C.*Mínima:\\s*22\\.8°C.*Días sobre promedio:\\s*3.*"
}

print(f"\nTest configurado:")
print(f"  Input: {repr(test_corregido['input'])}")
print(f"  Expected (regex): {test_corregido['expected']}")

# Ejecutar código
stdout, stderr, exec_time = execute_python_code(codigo_usuario, test_corregido['input'])

if stderr:
    print(f"\n❌ ERROR: {stderr}")
else:
    print(f"\nOutput generado:")
    print("-" * 40)
    print(stdout)
    print("-" * 40)
    
    # Verificar con regex (CON re.DOTALL)
    if re.search(test_corregido['expected'], stdout, re.DOTALL):
        print(f"\n✅ TEST PASADO (tiempo: {exec_time}ms)")
        print("\n🎉 El test ahora funciona correctamente!")
    else:
        print(f"\n❌ TEST FALLÓ")
        print(f"\nPattern esperado: {test_corregido['expected']}")
        print(f"Output recibido: {repr(stdout)}")

print("\n" + "="*70)
print("RESUMEN")
print("="*70)
print("✅ Test ANTES (incorrecto):")
print("   promedio == 24.44 and temp_max == 26.0 and ...")
print("   ❌ Intentaba evaluar variables fuera de scope")
print()
print("✅ Test AHORA (correcto):")
print("   .*Promedio:\\\\s*24\\\\.4[34]°C.*Máxima:\\\\s*26\\\\.0°C...")
print("   ✅ Verifica el OUTPUT con regex pattern")
print("="*70 + "\n")
