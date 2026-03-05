from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal

from database import get_pool
from schemas import ClienteCreate, ContratoCreate

router = APIRouter()


# ─────────────── Schema de entrada unificado ───────────────

class OnboardingIn(BaseModel):
    # Dados do cliente
    nome: str
    modalidade: str
    dia_vencimento: int
    telefone: Optional[str] = None
    email: Optional[str] = None
    cpf_cnpj: Optional[str] = None

    # Dados do contrato
    valor_enviado: Decimal
    montante: Decimal
    spread_total: Optional[Decimal] = None
    num_parcelas: int
    taxa_mensal: Optional[Decimal] = None
    valor_parcela: Decimal
    spread_por_parcela: Optional[Decimal] = None
    data_inicio: Optional[date] = None  # default = hoje


# ─────────────── Rota POST /onboarding ───────────────

@router.post("/", status_code=201)
async def onboarding(payload: OnboardingIn):
    """
    Cadastra cliente + contrato e já gera todas as parcelas em uma única chamada.
    """
    pool = get_pool()

    # Validações antecipadas
    if not (1 <= payload.dia_vencimento <= 28):
        raise HTTPException(400, "dia_vencimento deve estar entre 1 e 28")
    if payload.num_parcelas < 1:
        raise HTTPException(400, "num_parcelas deve ser >= 1")

    data_inicio = payload.data_inicio or date.today()

    async with pool.acquire() as conn:
        async with conn.transaction():

            # 1. Cria o cliente
            cliente = await conn.fetchrow(
                """
                INSERT INTO clientes (nome, modalidade, dia_vencimento, telefone, email, cpf_cnpj)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *
                """,
                payload.nome,
                payload.modalidade,
                payload.dia_vencimento,
                payload.telefone,
                payload.email,
                payload.cpf_cnpj,
            )

            # 2. Cria o contrato
            contrato = await conn.fetchrow(
                """
                INSERT INTO contratos
                    (cliente_id, valor_enviado, montante, spread_total, num_parcelas,
                     taxa_mensal, valor_parcela, spread_por_parcela, data_inicio)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
                RETURNING *
                """,
                cliente["id"],
                payload.valor_enviado,
                payload.montante,
                payload.spread_total,
                payload.num_parcelas,
                payload.taxa_mensal,
                payload.valor_parcela,
                payload.spread_por_parcela,
                data_inicio,
            )

            # 3. Gera as parcelas
            parcelas = []
            for i in range(payload.num_parcelas):
                # Avança mês a mês a partir da data de início,
                # fixando o dia de vencimento do cliente
                vencimento_base = data_inicio + relativedelta(months=i + 1)
                data_vencimento = vencimento_base.replace(day=payload.dia_vencimento)
                mes_referencia = data_vencimento.strftime("%Y-%m")

                parcela = await conn.fetchrow(
                    """
                    INSERT INTO parcelas
                        (contrato_id, numero_parcela, total_parcelas,
                         mes_referencia, data_vencimento, valor, status)
                    VALUES ($1, $2, $3, $4, $5, $6, 'pendente')
                    RETURNING *
                    """,
                    contrato["id"],
                    i + 1,
                    payload.num_parcelas,
                    mes_referencia,
                    data_vencimento,
                    payload.valor_parcela,
                )
                parcelas.append(dict(parcela))

    return {
        "mensagem": "Cadastro realizado com sucesso",
        "cliente": dict(cliente),
        "contrato": dict(contrato),
        "parcelas_geradas": len(parcelas),
        "parcelas": parcelas,
    }