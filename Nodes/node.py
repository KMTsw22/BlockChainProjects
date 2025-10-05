from flask import Flask, request, jsonify
from Nodes.BlockChainClass import Blockchain
import json
import requests
import hashlib  # hash 함수용 sha256 사용할 라이브러리
import threading
import time

app = Flask(__name__)


class Node:
    def __init__(self, name, my_ip, my_port):
        self.blockchain = Blockchain()
        self.my_ip = my_ip
        self.my_port = my_port
        self.node_identifier = 'node' + my_port
        self.mine_owner = 'master'  # 보낼지갑주소
        self.mine_profit = 0.1  # 채굴보상값
        self.name = name
        self.app = Flask(name)
        self.is_mining = False
        self.stop_mining = threading.Event()
        self.mining_thread = None  # 스레드는 나중에 /mine 호출시 생성
        self.set_routes()

    def mining_loop(self):
        print("🟡 start mining...")
        while True:
            last_block = self.blockchain.last_block
            last_proof = last_block['nonce']
            self.stop_mining.clear()  # 채굴 시작 전 이벤트 초기화
            proof = self.blockchain.pow(last_proof, self.stop_mining)
            if proof is None:
                time.sleep(1)
                continue

            # 채굴 보상 지급
            self.blockchain.new_transaction(
                sender="master",
                recipient=self.node_identifier,
                amount=self.mine_profit
            )
            # 블록 생성
            previous_hash = self.blockchain.hash(last_block)
            block = self.blockchain.new_block(proof, previous_hash)
            print(f"✅ New block mined: index={block['index']} | txs={len(block['transactions'])}")
            # 다른 노드로 전파
            self.broadcast_new_block(block)
            time.sleep(1)

    def broadcast_new_block(self, block):
        for node in self.blockchain.nodes:
            try:
                data = {
                    "miner_node": f"http://{self.my_ip}:{self.my_port}",
                    "new_nonce": block['nonce'],
                    "new_block": block
                }
                requests.post(f"http://{node}/nodes/resolve", json=data, timeout=3)
            except Exception as e:
                print(f"⚠️ Failed to notify {node}: {e}")

    def set_routes(self):
        @self.app.route('/', methods=['GET'])
        def hi():
            print("chain info request")
            response = {
                'chain': self.blockchain.chain,
                'length': len(self.blockchain.chain),
                'ip_port': self.my_ip + ':' + self.my_port,
                'mine_owner': self.mine_owner,
                'name': self.name,
                'node_identifier': self.node_identifier,
                'node': len(self.blockchain.nodes)
            }
            return jsonify(response), 200

        @self.app.route('/chain', methods=['GET'])
        def full_chain():
            print("chain info request")
            response = {
                'chain': self.blockchain.chain,
                'length': len(self.blockchain.chain)
            }
            return jsonify(response), 200

        @self.app.route('/nodes/register', methods=['POST'])
        def register_nodes():
            values = request.get_json()
            print("registering nodes !!! : ", values)
            registering_node = values.get('nodes')
            if registering_node is None:
                return "ERROR : Please supply a valid list of nodes", 400
            if registering_node.split("//")[1] in self.blockchain.nodes:
                print("노드가 이미 있는 노드입니다.")
                response = {
                    "message": "Alrealy register",
                    "total_nodes": list(self.blockchain.nodes)
                }
            else:
                self.blockchain.register_node(registering_node)
                headers = {'Content-Type': 'application/json; charset=utf-8'}
                data = {"nodes": 'http://' + self.my_ip + ":" + self.my_port}
                print("MY NODE INFO ", 'http://' + self.my_ip + ":" + self.my_port)
                requests.post(registering_node + "/nodes/register", headers=headers, data=json.dumps(data))

                # 이후 주변 노드들에도 새로운 노드가 등장함을 전파
                for add_node in self.blockchain.nodes:
                    if add_node != registering_node.split("//")[1]:  # ip:port
                        print('add_node : ', add_node)
                        headers = {'Content-Type': 'application/json; charset=utf-8'}
                        data = {"nodes": registering_node}
                        requests.post('http://' + add_node + "/nodes/register", headers=headers, data=json.dumps(data))

                response = {
                    'message': 'New nodes have been added',
                    'total_nodes': list(self.blockchain.nodes),
                }
            return jsonify(response), 201

        @self.app.route('/transactions/new', methods=['POST'])
        def new_transaction():
            values = request.get_json()
            required = ['sender', 'recipient', 'amount']
            if not all(k in values for k in required):
                return 'Missing values', 400
            index = self.blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])
            response = {
                'message': f'Transaction queued for next block (index {index})'
            }
            return jsonify(response), 201

        @self.app.route("/nodes/resolve", methods=['POST'])
        def resolve():
            requester_node_info = request.get_json()
            required = ["miner_node"]
            print("전파 시작 from", required)

            my_previous_hash = self.blockchain.last_block['previous_hash']
            last_proof = self.blockchain.last_block["nonce"]

            headers = {'Content-Type': 'application/json; charset=utf-8'}
            miner_block_info = requests.get(requester_node_info['miner_node'] + "/chain", headers=headers)

            new_block_previous_hash = json.loads(miner_block_info.text)['chain'][-2]['previous_hash']

            if new_block_previous_hash == my_previous_hash \
                    and hashlib.sha256(str(last_proof + int(requester_node_info['new_nonce'])).encode()).hexdigest()[
                :4] == "0000":
                print("다른 노드에서 요청이 온 블럭 :: 검증결과 정상.")
                replaced = self.blockchain.resolve_conflict()
                if replaced:
                    print("내 체인이 짧아서 교체댐 length", len(self.blockchain.chain))
                    response = {'message': 'Our chain was replaced >> ' + self.my_ip + ":" + self.my_port,
                                'new_chain': self.blockchain.chain}
                else:
                    response = {'message': 'Our chain is authoritative', 'chain': self.blockchain.chain}
            else:
                print("경쟁 블록 발생! 이전 해시가 맞지 않거나 POW 검증 실패")
                replaced = self.blockchain.resolve_conflict()
                if replaced:
                    print("내체인이 더약함 잡아먹힘")
                    response = {'message': 'Chain replaced due to longer chain detected',
                                'new_chain': self.blockchain.chain}
                else:
                    print("내 체인이 더 쎔으로 그냥 둠")
                    response = {'message': 'Chain maintained; a fork exists but authoritative chain kept',
                                'chain': self.blockchain.chain}

            self.stop_mining.set()             # 채굴 중단 신호 전달 이거 위에 채굴중인 POW안에서 그 while문 종료하고 나오도록 그리고 다시 재채굴시도시작
            return jsonify(response), 200

        # 🔹 새로운 /mine 라우트 추가
        @self.app.route('/mine', methods=['GET'])
        def mine():
            if self.is_mining:
                return jsonify({'message': 'Mining already in progress'}), 400
            self.stop_mining.clear()
            self.mining_thread = threading.Thread(target=self.mining_loop, daemon=True)
            self.is_mining = True
            self.mining_thread.start()
            return jsonify({'message': 'Mining started'}), 200

    def run(self):
        print(f"✅ Node '{self.name}' running at http://{self.my_ip}:{self.my_port}")
        self.app.run(host=self.my_ip, port=self.my_port)