"""
Script para crear usuarios de prueba en la base de datos
"""
import sys
from pathlib import Path

# Agregar backend al path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from backend.database import get_db_session, UserRepository
from backend.models.user import UserRole
from backend.core.security import hash_password

def create_test_users():
    """Crea usuarios de prueba para desarrollo"""
    print("=" * 80)
    print("CREANDO USUARIOS DE PRUEBA")
    print("=" * 80)

    # Obtener sesión de base de datos usando context manager
    with get_db_session() as db:
        user_repo = UserRepository(db)
        # Usuarios de prueba
        # FIX Cortez79: Updated credentials to match frontend LoginPage.tsx
        # Frontend shows: student@activia.com / Student1234 and teacher@activia.com / Teacher1234
        test_users = [
            {
                "email": "demo@activia.com",
                "password": "demo123",
                "full_name": "Usuario Demo",
                "role": UserRole.STUDENT,
            },
            {
                "email": "student@activia.com",
                "password": "Student1234",  # FIX: Match frontend credentials
                "full_name": "Estudiante Prueba",
                "role": UserRole.STUDENT,
            },
            {
                "email": "teacher@activia.com",  # FIX: Add teacher user
                "password": "Teacher1234",
                "full_name": "Docente Prueba",
                "role": UserRole.TEACHER,
            },
            {
                "email": "tutor@activia.com",
                "password": "tutor123",
                "full_name": "Tutor Prueba",
                "role": UserRole.TUTOR,
            },
            {
                "email": "admin@activia.com",
                "password": "admin123",
                "full_name": "Administrador",
                "role": UserRole.ADMIN,
            },
        ]

        created_count = 0
        for user_data in test_users:
            # Verificar si el usuario ya existe
            existing = user_repo.get_by_email(user_data["email"])
            if existing:
                print(f"⚠️  Usuario ya existe: {user_data['email']}")
                continue

            # Crear usuario
            from backend.database.models import UserDB
            # Generar username desde email (antes del @)
            username = user_data["email"].split("@")[0]
            user = UserDB(
                email=user_data["email"],
                username=username,
                hashed_password=hash_password(user_data["password"]),
                full_name=user_data["full_name"],
                roles=[user_data["role"].value] if isinstance(user_data["role"], UserRole) else [user_data["role"]],
                is_active=True,
            )
            db.add(user)
            created_count += 1
            print(f"✅ Creado: {user_data['email']} ({user_data['role']}) - password: {user_data['password']}")

        print("\n" + "=" * 80)
        print(f"COMPLETADO: {created_count} usuarios creados")
        print("=" * 80)
        print("\nCREDENCIALES DE PRUEBA:")
        print("   - demo@activia.com / demo123 (STUDENT)")
        print("   - student@activia.com / Student1234 (STUDENT)")
        print("   - teacher@activia.com / Teacher1234 (TEACHER)")
        print("   - tutor@activia.com / tutor123 (TUTOR)")
        print("   - admin@activia.com / admin123 (ADMIN)")
        print()

if __name__ == "__main__":
    create_test_users()
