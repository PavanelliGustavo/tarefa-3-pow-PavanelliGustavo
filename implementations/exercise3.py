import csv
import hashlib
import multiprocessing
import os
import struct
import time


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


VERSION    = (2).to_bytes(4, "big")
PREV_BLOCK = bytes.fromhex("00000000d1145790a8694403d4063f323d499e655c83426834d4ce2f8dd4a2ee")
TIMESTAMP  = 1231361565   # dentro do intervalo válido de Jan 2009
# Target: hash deve ter os primeiros 4 bytes = 0x00000000
TARGET_INT = 0x00000000FFFF0000000000000000000000000000000000000000000000000000


def _mine_worker(worker_id: int, n_workers: int,
                 fixed64_hex: str, fixed_tail_hex: str,
                 result_q) -> None:
    """
    Cada worker testa nonces: worker_id, worker_id+n_workers, worker_id+2*n_workers, ...
    Usa o truque de pré-hashear os primeiros 64 bytes do header (que são fixos)
    e só processar os últimos 16 bytes por iteração.
    """
    fixed64    = bytes.fromhex(fixed64_hex)
    fixed_tail = bytes.fromhex(fixed_tail_hex)   # 8 bytes fixos (fin. da merkle_root + timestamp)
    h0         = hashlib.sha256(fixed64)          # estado SHA256 após os primeiros 64 bytes
    buf        = bytearray(fixed_tail) + bytearray(8)   # 16 bytes: tail(8) + nonce(8)
    nonce      = worker_id

    while True:
        struct.pack_into(">Q", buf, 8, nonce)   # escreve o nonce (8 bytes big-endian) no buf
        h = h0.copy()
        h.update(buf)
        d = h.digest()
        # Condição rápida: os 4 primeiros bytes devem ser zero
        if d[0] == 0 and d[1] == 0 and d[2] == 0 and d[3] == 0:
            result_q.put(nonce)
            return
        nonce += n_workers


def solution(merkle_root_hex: str) -> None:
    print("Exercício 3: minerando o cabeçalho do bloco (pode levar alguns minutos)...")
    t0 = time.time()

    merkle_bytes  = bytes.fromhex(merkle_root_hex)
    ts_bytes      = TIMESTAMP.to_bytes(4, "big")
    # Prefixo fixo: version(4) + prevhash(32) + merkleroot(32) + timestamp(4) = 72 bytes
    header_prefix = VERSION + PREV_BLOCK + merkle_bytes + ts_bytes

    # Divide no limite do bloco SHA256 (64 bytes):
    #   fixed64   = bytes 0-63  → sempre no primeiro bloco de hash (todos fixos)
    #   fixed_tail = bytes 64-71 → 8 bytes fixos antes do nonce
    fixed64    = header_prefix[:64]
    fixed_tail = header_prefix[64:]   # = merkleroot[28:32] + timestamp = 8 bytes

    n_workers = os.cpu_count() or 4
    print(f"  Usando {n_workers} processos em paralelo...")

    result_q = multiprocessing.Queue()
    workers  = [
        multiprocessing.Process(
            target=_mine_worker,
            args=(i, n_workers, fixed64.hex(), fixed_tail.hex(), result_q),
        )
        for i in range(n_workers)
    ]
    for w in workers:
        w.start()

    nonce = result_q.get()   # bloqueia até um worker encontrar o nonce

    for w in workers:
        w.terminate()
    for w in workers:
        w.join()

    header     = header_prefix + nonce.to_bytes(8, "big")
    block_hash = sha256(header).hex()
    elapsed    = time.time() - t0

    print(f"  Nonce encontrado: {nonce}")
    print(f"  Tempo: {elapsed:.1f}s")
    print(f"  Hash do bloco: {block_hash}")

    with open("solutions/exercise03.txt", "w") as f:
        f.write(header.hex())

solution()