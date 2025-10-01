from dao.database import SessionLocal
from dao.campus_dao import CampusDAO

def criar_campus_iniciais():
    """Cria campus iniciais no sistema"""
    db = SessionLocal()
    try:
        # Verificar se já existem campus
        campus_existentes = CampusDAO.get_all(db)
        if campus_existentes:
            print("Campus já existem no sistema.")
            return
        
        # Criar campus iniciais
        campus_data = [
            {"nome": "Campus Boa Viagem", "endereco": "Rodovia Pres. Juscelino Kubitschek (BR 020), km 209 - Boa Viagem - CE"},
            {"nome": "Campus Recife", "endereco": "R. do Príncipe, 526 - Boa Vista, Recife - PE"},
            {"nome": "Campus Jaboatão dos Guararapes", "endereco": "R. Cícero de Arruda, 300 - Jaboatão dos Guararapes - PE"},
            {"nome": "Campus Olinda", "endereco": "R. do Bonfim, 47 - Carmo, Olinda - PE"},
            {"nome": "Campus Vitória de Santo Antão", "endereco": "R. do Bonfim, 47 - Carmo, Vitória de Santo Antão - PE"}
        ]
        
        for campus_info in campus_data:
            CampusDAO.create(
                db=db,
                nome=campus_info["nome"],
                endereco=campus_info["endereco"]
            )
            print(f"Campus '{campus_info['nome']}' criado com sucesso.")
        
        print("Todos os campus iniciais foram criados com sucesso!")
        
    except Exception as e:
        print(f"Erro ao criar campus: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    criar_campus_iniciais()
