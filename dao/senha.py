from passlib.hash import bcrypt

# Gerar hash da senha
senha = "@dipe2025"
senha_hash = bcrypt.hash(senha)

print(f"Senha criptografada: {senha_hash}")