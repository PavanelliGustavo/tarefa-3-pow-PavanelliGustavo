import csv
import hashlib
import multiprocessing
import os
import struct
import time


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()

PROOF_TXID = "49ff8cccf1ca12179e9ae7a4760f550b5a18401b27e1e057604e27c3e10c08fb"


def _merkle_levels(leaves: list) -> list:
    """
    Constrói a Merkle tree nível a nível.
    Retorna lista de níveis: levels[0] = folhas, levels[-1] = [raiz].
    """
    levels  = [leaves[:]]
    current = leaves[:]
    while len(current) > 1:
        if len(current) % 2 == 1:
            current.append(current[-1])   # duplica o último se ímpar
        current = [sha256(current[i] + current[i + 1]) for i in range(0, len(current), 2)]
        levels.append(current[:])
    return levels


def solution() -> str:
    print("Exercício 2: calculando Merkle root e prova de inclusão...")
    with open("data/ex02_txid_list.txt") as f:
        txids = [ln.strip() for ln in f if ln.strip()]

    leaves = [bytes.fromhex(tx) for tx in txids]
    levels = _merkle_levels(leaves)
    root   = levels[-1][0]

    # Localiza o índice da transação-alvo na folha
    target_bytes = bytes.fromhex(PROOF_TXID)
    idx          = levels[0].index(target_bytes)

    # Coleta os "irmãos" (siblings) de cada nível, da folha até a raiz
    proof = []
    for level in levels[:-1]:
        padded      = level + ([level[-1]] if len(level) % 2 == 1 else [])
        sibling_idx = idx ^ 1   # XOR 1 alterna entre par/ímpar para achar o irmão
        proof.append(padded[sibling_idx])
        idx //= 2

    root_hex = root.hex()
    print(f"  Merkle root: {root_hex}")
    print(f"  Profundidade da prova: {len(proof)} níveis")

    with open("solutions/exercise02.txt", "w") as f:
        f.write(root_hex + "\n")
        for sibling in proof:
            f.write(sibling.hex() + "\n")

    return root_hex

solution()