import csv
import hashlib
import multiprocessing
import os
import struct
import time


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


REQUIRED_TXID = "4c50e3dad7f98bceb6441f96b23748dea84fbdb7cedd603441e6ea4a574d04a6"
WEIGHT_LIMIT  = 4_000_000


def _parse_mempool() -> dict:
    mempool: dict = {}
    with open("data/mempool.csv", newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            txid    = row[0].strip()
            fee     = int(row[1])
            weight  = int(row[2])
            raw     = row[3].strip() if len(row) >= 4 else ""
            parents = [p.strip() for p in raw.split(";") if p.strip()]
            mempool[txid] = {"fee": fee, "weight": weight, "parents": parents}
    return mempool


def _ancestors_in_order(txid: str, mempool: dict) -> list:
    """
    Retorna txid + todos os seus ancestrais em ordem topológica (pais antes dos filhos).
    Usa DFS iterativo para evitar limite de recursão.
    """
    result    = []
    completed = set()   # transações já adicionadas ao resultado
    visiting  = set()   # transações cujo DFS já foi iniciado
    stack     = [txid]

    while stack:
        tx = stack[-1]
        if tx not in mempool or tx in completed:
            stack.pop()
            continue
        if tx not in visiting:
            visiting.add(tx)
            for parent in mempool[tx]["parents"]:
                if parent not in completed and parent not in visiting:
                    stack.append(parent)
        else:
            stack.pop()
            if tx not in completed:
                completed.add(tx)
                result.append(tx)

    return result


def solution() -> list:
    print("Exercício 1: selecionando transações do mempool...")
    mempool = _parse_mempool()

    selected     : list = []
    included     : set  = set()
    total_weight : int  = 0

    def add_package(txid: str) -> bool:
        nonlocal total_weight
        package  = _ancestors_in_order(txid, mempool)
        new_txs  = [tx for tx in package if tx not in included]
        delta    = sum(mempool[tx]["weight"] for tx in new_txs)
        if total_weight + delta > WEIGHT_LIMIT:
            return False
        for tx in new_txs:
            selected.append(tx)
            included.add(tx)
        total_weight += delta
        return True

    # Transação obrigatória primeiro (com todos os seus ancestrais)
    if not add_package(REQUIRED_TXID):
        raise RuntimeError("Transação obrigatória + ancestrais excedem o limite de peso")

    # Candidatas restantes ordenadas por fee/weight decrescente (taxa por unidade de espaço)
    candidates = sorted(
        (tx for tx in mempool if tx not in included),
        key=lambda tx: mempool[tx]["fee"] / mempool[tx]["weight"],
        reverse=True,
    )
    for txid in candidates:
        if txid not in included:
            add_package(txid)

    total_fee = sum(mempool[tx]["fee"] for tx in selected)
    print(f"  {len(selected)} transações | peso {total_weight:,} | taxas {total_fee:,} sats")

    with open("solutions/exercise01.txt", "w") as f:
        f.write("\n".join(selected))

    return selected

solution()