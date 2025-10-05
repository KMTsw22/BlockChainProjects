import requests
import json
import time

# --------------------------------------
# 요청 함수 정의 (기존 코드 활용)
# --------------------------------------
def RequestRegister(send, receive):
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    data = {
        "nodes": f"http://127.0.0.1:{receive}"
    }
    res = requests.post(f"http://127.0.0.1:{send}/nodes/register", headers=headers, data=json.dumps(data))
    print(res.content)

def RequestInputTransaction():
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    body = {"sender": "mintae", "recipient": "mintae2", "amount": 3}
    ports = ['5000', '5001']
    for port in ports:
        res = requests.post(f"http://127.0.0.1:{port}/transactions/new", headers=headers, data=json.dumps(body))
        print(res.content)

def RequestMineStart(port):
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    res = requests.get(f"http://127.0.0.1:{port}/mine", headers=headers)
    print(res.content)

# --------------------------------------
# 1. 노드 등록
# --------------------------------------
print("🔗 서로 노드 등록 중...")
RequestRegister('5000', '5001')
time.sleep(1)  # 안정성을 위해 약간의 대기



# --------------------------------------
# 3. 채굴 시작
# --------------------------------------
print("⛏ 채굴 시작...")
# 5000과 5001 동시에 채굴 시작
for port in ['5000', '5001']:
    RequestMineStart(port)
