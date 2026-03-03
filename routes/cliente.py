from fastapi import APIRouter, HTTPException
from typing import List, Optional
from database import get_pool
from schemas import ClienteCreate, ClienteUpdate, ClienteOut

router = APIRouter()


@router.get("/", response_model=List[ClienteOut])
async def listar_clientes(
    modalidade: Optional[str] = None,
    ativo: Optional[bool] = True,
    search: Optional[str] = None,
):
    pool = get_pool()
    conditions = ["1=1"]
    args = []

    if ativo is not None:
        args.append(ativo)
        conditions.append(f"ativo = ${len(args)}")
    if modalidade:
        args.append(modalidade)
        conditions.append(f"modalidade = ${len(args)}")
    if search:
        args.append(f"%{search}%")
        conditions.append(f"nome ILIKE ${len(args)}")

    where = " AND ".join(conditions)
    rows = await pool.fetch(
        f"SELECT * FROM clientes WHERE {where} ORDER BY nome", *args
    )
    return [dict(r) for r in rows]


@router.get("/{cliente_id}", response_model=ClienteOut)
async def buscar_cliente(cliente_id: int):
    pool = get_pool()
    row = await pool.fetchrow("SELECT * FROM clientes WHERE id = $1", cliente_id)
    if not row:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return dict(row)


@router.post("/", response_model=ClienteOut, status_code=201)
async def criar_cliente(payload: ClienteCreate):
    pool = get_pool()
    row = await pool.fetchrow(
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
    return dict(row)


@router.patch("/{cliente_id}", response_model=ClienteOut)
async def atualizar_cliente(cliente_id: int, payload: ClienteUpdate):
    pool = get_pool()
    data = payload.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    sets = ", ".join(f"{k} = ${i+2}" for i, k in enumerate(data.keys()))
    values = list(data.values())
    row = await pool.fetchrow(
        f"UPDATE clientes SET {sets} WHERE id = $1 RETURNING *",
        cliente_id,
        *values,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return dict(row)


@router.delete("/{cliente_id}", status_code=204)
async def desativar_cliente(cliente_id: int):
    """Soft delete — apenas marca como inativo."""
    pool = get_pool()
    result = await pool.execute(
        "UPDATE clientes SET ativo = FALSE WHERE id = $1", cliente_id
    )
    if result == "UPDATE 0":
        raise HTTPException(status_code=404, detail="Cliente não encontrado")


@router.get("/{cliente_id}/contratos")
async def contratos_do_cliente(cliente_id: int):
    pool = get_pool()
    rows = await pool.fetch(
        "SELECT * FROM contratos WHERE cliente_id = $1 ORDER BY id", cliente_id
    )
    return [dict(r) for r in rows]


@router.get("/{cliente_id}/parcelas")
async def parcelas_do_cliente(cliente_id: int, status: Optional[str] = None):
    pool = get_pool()
    query = """
        SELECT p.*, c.nome AS cliente_nome, ct.valor_parcela
        FROM parcelas p
        JOIN contratos ct ON ct.id = p.contrato_id
        JOIN clientes c ON c.id = ct.cliente_id
        WHERE c.id = $1
    """
    args = [cliente_id]
    if status:
        args.append(status)
        query += f" AND p.status = ${len(args)}"
    query += " ORDER BY p.data_vencimento"

    rows = await pool.fetch(query, *args)
    return [dict(r) for r in rows]