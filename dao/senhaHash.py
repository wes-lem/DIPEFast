import bcrypt

def criptografar_senha(senha_texto_plano):
    """
    Criptografa uma senha usando bcrypt e exibe o hash gerado.
    """
    # 1. A senha precisa ser convertida para o formato de bytes (padrão utf-8)
    senha_em_bytes = senha_texto_plano.encode('utf-8')
    
    # 2. Gera um "salt" aleatório. O salt garante que o mesmo password
    #    gere um hash diferente a cada vez, aumentando a segurança.
    salt = bcrypt.gensalt()
    
    # 3. Criptografa a senha (hash) usando o salt gerado
    hash_gerado = bcrypt.hashpw(senha_em_bytes, salt)
    
    # 4. Exibe o resultado no console
    # O hash é retornado em bytes, então o decodificamos para exibir como texto
    print(f"Senha original: {senha_texto_plano}")
    print(f"Hash Bcrypt gerado: {hash_gerado.decode('utf-8')}")

# Chame a função com a senha que você deseja criptografar
if __name__ == "__main__":
    criptografar_senha("@dipe2025")