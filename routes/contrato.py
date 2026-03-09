from fastapi import APIRouter, HTTPException
from typing import List, Optional
from database import get_pool
from schemas import ContratoCreate, ContratoUpdate, ContratoOut

router = APIRouter()

# contrato.py: rota para gerenciar contratos (CRUD + listagem de parcelas)
@router.get("/", response_model=List[ContratoOut])
async def listar_contratos(ativo: Optional[bool] = True):
    pool = get_pool()
    rows = await pool.fetch(
        "SELECT * FROM contratos WHERE ativo = $1 ORDER BY id", ativo
    )
    return [dict(r) for r in rows]


@router.get("/{contrato_id}", response_model=ContratoOut)
async def buscar_contrato(contrato_id: int):
    pool = get_pool()
    row = await pool.fetchrow("SELECT * FROM contratos WHERE id = $1", contrato_id)
    if not row:
        raise HTTPException(status_code=404, detail="Contrato não encontrado")
    return dict(row)


@router.post("/", response_model=ContratoOut, status_code=201)
async def criar_contrato(payload: ContratoCreate):
    pool = get_pool()
    # Verifica se cliente existe
    cliente = await pool.fetchrow(
        "SELECT id FROM clientes WHERE id = $1", payload.cliente_id
    )
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    row = await pool.fetchrow(
        """
        INSERT INTO contratos
            (cliente_id, valor_enviado, montante, spread_total, num_parcelas,
             taxa_mensal, valor_parcela, spread_por_parcela, data_inicio)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
        RETURNING *
        """,
        payload.cliente_id,
        payload.valor_enviado,
        payload.montante,
        payload.spread_total,
        payload.num_parcelas,
        payload.taxa_mensal,
        payload.valor_parcela,
        payload.spread_por_parcela,
        payload.data_inicio,
    )
    return dict(row)


@router.patch("/{contrato_id}", response_model=ContratoOut)
async def atualizar_contrato(contrato_id: int, payload: ContratoUpdate):
    pool = get_pool()
    data = payload.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    sets = ", ".join(f"{k} = ${i+2}" for i, k in enumerate(data.keys()))
    values = list(data.values())
    row = await pool.fetchrow(
        f"UPDATE contratos SET {sets} WHERE id = $1 RETURNING *",
        contrato_id,
        *values,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Contrato não encontrado")
    return dict(row)


@router.delete("/{contrato_id}", status_code=204)
async def desativar_contrato(contrato_id: int):
    pool = get_pool()
    result = await pool.execute(
        "UPDATE contratos SET ativo = FALSE WHERE id = $1", contrato_id
    )
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Contrato não encontrado")


@router.get("/{contrato_id}/parcelas")
async def parcelas_do_contrato(contrato_id: int, status: Optional[str] = None):
    pool = get_pool()
    query = "SELECT * FROM parcelas WHERE contrato_id = $1"
    args = [contrato_id]
    if status:
        args.append(status)
        query += f" AND status = ${len(args)}"
    query += " ORDER BY data_vencimento"
    rows = await pool.fetch(query, *args)
    return [dict(r) for r in rows]