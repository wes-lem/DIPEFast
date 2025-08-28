from models.aluno import Aluno

class AlunoDAO:
    @staticmethod
    def create(db, idUser, nome, ano, curso, imagem=None, idade=None, municipio=None, zona=None, origem_escolar=None, escola=None, forma_ingresso=None, acesso_internet=None, observacoes=None):
        aluno = Aluno(
            idUser=idUser,
            nome=nome,
            ano=ano,
            curso=curso,
            imagem=imagem,
            idade=idade,
            municipio=municipio,
            zona=zona,
            origem_escolar=origem_escolar,
            escola=escola,
            forma_ingresso=forma_ingresso,
            acesso_internet=acesso_internet,
            observacoes=observacoes
        )
        db.add(aluno)
        db.commit()
        db.refresh(aluno)
        return aluno
