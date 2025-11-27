"""
Serviço para cálculo de notas e classificação de situações das provas
"""

def calcular_nota_e_situacao(acertos: int, total_questoes: int) -> tuple[float, str]:
    """
    Calcula a nota (0-10) e determina a situação baseada nos acertos
    
    Args:
        acertos: Número de acertos do aluno
        total_questoes: Total de questões da prova
        
    Returns:
        tuple: (nota, situacao) onde nota é de 0.0 a 10.0
    """
    if total_questoes == 0:
        return 0.0, "Insuficiente"
    
    # Calcular nota de 0 a 10
    nota = (acertos / total_questoes) * 10
    
    # Determinar situação baseada na nota
    if nota <= 5:
        situacao = "Insuficiente"
    elif nota < 8:
        situacao = "Regular"
    else:  # nota >= 8
        situacao = "Suficiente"
    
    return round(nota, 2), situacao

def classificar_situacao_por_nota(nota: float) -> str:
    """
    Classifica a situação baseada apenas na nota
    
    Args:
        nota: Nota de 0.0 a 10.0
        
    Returns:
        str: Situação do aluno
    """
    if nota <= 5:
        return "Insuficiente"
    elif nota < 8:
        return "Regular"
    else:  # nota >= 8
        return "Suficiente"
