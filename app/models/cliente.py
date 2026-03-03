from sqlalchemy import Column, Integer, String, Boolean, SmallInteger, TIMESTAMP
from sqlalchemy.sql import func
from app.database.base import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(200), nullable=False)
    modalidade = Column(String(50))
    dia_vencimento = Column(SmallInteger, nullable=False)
    telefone = Column(String(20))
    email = Column(String(100))
    cpf_cnpj = Column(String(20))
    ativo = Column(Boolean, default=True)
    criado_em = Column(TIMESTAMP, server_default=func.now())