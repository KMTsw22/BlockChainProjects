from node import Node
# 여러 노드를 한 파일에서 실행할 때
if __name__ == '__main__':
    Node1 = Node("node1","127.0.0.1", "5000")
    Node1.run()