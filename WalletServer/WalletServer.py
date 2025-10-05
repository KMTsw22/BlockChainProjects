from flask import Flask
from datetime import datetime
from flask import render_template
from flask import request
from flask import url_for
from flask import redirect

import requests
import json
import os
import pandas as pd

app = Flask(__name__, template_folder=os.getcwd())


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        print("login 버튼을 누름")
        input_value = request.form.to_dict(flat=False)['wallet_id'][0]
        print("login 지갑주소 : ", input_value)
        ### 기존 user 정보 확인
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        res = requests.get("http://127.0.0.1:5000/chain", headers=headers)
        status_json = json.loads(res.text)
        status_json['chain']
        tx_amount_l = []
        tx_sender_l = []
        tx_reciv_l = []
        tx_time_l = []
        # 거래내역 정리 (df_tx)
        for chain_index in range(len(status_json['chain'])):
            chain_tx = status_json['chain'][chain_index]['transactions']
            for each_tx in range(len(chain_tx)):
                tx_amount_l.append(chain_tx[each_tx]['amount'])
                tx_sender_l.append(chain_tx[each_tx]['sender'])
                tx_reciv_l.append(chain_tx[each_tx]['recipient'])
                tx_time_l.append(chain_tx[each_tx]['timestamp'])
        df_tx = pd.DataFrame()
        df_tx['timestamp'] = tx_time_l
        df_tx['sender'] = tx_sender_l
        df_tx['recipient'] = tx_reciv_l
        df_tx['amount'] = tx_amount_l
        df_tx

        # pyBTC 잔고현황 정리 (df_status)
        df_sended = pd.DataFrame(df_tx.groupby('sender')['amount'].sum()).reset_index()
        df_sended.columns = ['user', 'sended_amount']
        df_received = pd.DataFrame(df_tx.groupby('recipient')['amount'].sum()).reset_index()
        df_received.columns = ['user', 'received_amount']
        df_status = pd.merge(df_received, df_sended, on='user', how='outer').fillna(0)
        df_status['balance'] = df_status['received_amount'] - df_status['sended_amount']
        df_status

        # 결과값 랜더링
        if (df_status['user'] == input_value).sum() == 1:
            print("로그인성공")
            return render_template("wallet.html", wallet_id=input_value,
                                   wallet_value=df_status[df_status['user'] == input_value]['balance'].iloc[0])
        else:
            return "잘못된 지갑주소입니다."

    return render_template('login.html')


@app.route('/wallet', methods=['GET', 'POST'])
def wallet():
    if request.method == 'POST':
        send_value = int(request.form.to_dict(flat=False)['send_value'][0])
        send_target = request.form.to_dict(flat=False)['send_target'][0]
        send_from = request.form.to_dict(flat=False)['send_from'][0]
        print("Login Wallet ID : ", send_from)

        if send_value > 0:
            print("Send Amout :", send_value)
            ## transaction 입력하기
            headers = {'Content-Type': 'application/json; charset=utf-8'}
            data = {
                "sender": send_from,
                "recipient": send_target,
                "amount": send_value,
            }
            requests.post("http://127.0.0.1:5000/transactions/new", headers=headers, data=json.dumps(data))

            return "전송 완료!"

        else:
            return "0 pyBTC 이상 보내주세요!"

    return render_template('wallet.html')

app.run(port=8081)