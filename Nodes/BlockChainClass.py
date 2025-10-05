from flask import Flask, request, jsonify
from urllib.parse import urlparse
import json
import requests
import hashlib
import threading
import time
import random

# ------------------------- Blockchain 클래스 -------------------------
class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []  # 블록 생성되기 전에 거래내역 저장
        self.nodes = set()              # 노드 저장
        self.new_block(previous_hash=1, proof=100)  # 제네시스 블록 생성

    # 해시 암호화 함수
    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    # 마지막 블록 호출
    @property
    def last_block(self):
        return self.chain[-1]

    # 블록 검증 함수
    @staticmethod
    def valid_proof(last_proof, proof):
        guess = str(last_proof + proof).encode()  # 전 proof와 새 proof 연결
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    # 작업증명 함수 POW
    def pow(self, last_proof, stop_event=None):
        proof = random.randint(-100000, 100000)
        cnt = 0
        while not self.valid_proof(last_proof, proof):
            if stop_event and stop_event.is_set():   # 중단 신호 감지
                print("⛔ 채굴 중단 감지 — 다른 노드가 블록을 먼저 채굴했습니다.")
                return None
            proof = random.randint(-100000, 100000)
            cnt += 1
            if cnt % 1000 == 0:
                print(cnt)
            time.sleep(0.0001)
        return proof

    # 거래 내역 추가 함수
    def new_transaction(self, sender, recipient, amount):
        self.current_transactions.append(
            {
                "sender": sender,
                "recipient": recipient,
                "amount": amount,
                "timestamp": time.time()
            }
        )
        return self.last_block['index'] + 1

    # 신규 블록 생성 함수
    def new_block(self, proof=None, previous_hash=None):
        block = {
            "index": len(self.chain) + 1,
            "timestamp": time.time(),
            "transactions": self.current_transactions,
            "nonce": proof,
            "previous_hash": previous_hash or self.hash(self.last_block),
        }
        self.current_transactions = []  # 초기화
        self.chain.append(block)
        return block

    # 생성된 체인 검증 함수
    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            if block["previous_hash"] != self.hash(last_block):
                return False
            last_block = block
            current_index += 1
        return True

    # 노드 등록 함수
    def register_node(self, address):
        parse_url = urlparse(address)
        self.nodes.add(parse_url.netloc)

    # 체인 충돌 해결 함수
    def resolve_conflict(self):
        neighbours = self.nodes
        new_chain = None
        max_length = len(self.chain)

        for node in neighbours:
            node_url = "http://" + str(node.replace("0.0.0.0", "localhost")) + '/chain'
            try:
                response = requests.get(node_url, timeout=3)
            except:
                continue
            if response.status_code == 200:
                length = response.json()["length"]
                chain = response.json()["chain"]
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        if new_chain is not None:
            self.chain = new_chain
            return True
        return False