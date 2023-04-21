import pika
import chess
from chess import Board
import json

gamesDict: dict[str, Board] = {}

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost')
)

channel = connection.channel()

channel.queue_declare(queue='rpc_queue')

def isLegalMove(board: Board, move: str):
    for legalMove in board.legal_moves:
        if(board.san(legalMove) == move):
            return True
    return False

def isCheckmate(gameBoard: Board):
    return gameBoard.is_checkmate()

def isNewGame(request:str):
    rqVals = request.split(',')
    if(rqVals[0].lower().replace("b'", "") == 'new_game'):
        return True
    
def getKey(str1: str,str2:str):
    print(str1)
    print(str2)
    if str1.replace(" ", "")>str2.replace(" ", ""):
        return str1+str2
    else:
        return str2+str1
    
def makeMove(request):
    if(isNewGame(request)):
        rqVals = request.split(',')
        player1 = rqVals[1].replace("+1", "")
        player2 = rqVals[2].replace("+1", "")
        key = getKey(player1,player2)
        print(key)
        playerMove = rqVals[3].replace("'","").replace("\\","")
        newBoard = chess.Board()
        if(isLegalMove(newBoard, playerMove)):
            newBoard.push_san(playerMove)
            gamesDict[key] = newBoard
            gameOver = isCheckmate(newBoard)
            return json.dumps({
                "FEN": newBoard.fen(),
                "nextPlayer": player2,
                "moveMade": playerMove,
                "isGameOver": gameOver
            })
        else:
            return json.dumps({
               "FEN": "",
               "nextPlayer": player1,
               "moveMade": playerMove,
               "isGameOver": False
            })
    else:
        rqVals = request.split(',')
        player1 = rqVals[0].replace("+1", "").replace("b'", "")
        player2 = rqVals[1].replace("+1", "")
        playerMove = rqVals[2].replace("'","").replace("\\","")
        key = getKey(player1,player2)
        print(key)
        gameBoard = gamesDict[key]
        if(isLegalMove(gameBoard, playerMove)):
            gameBoard.push_san(playerMove)
            gameOver = isCheckmate(gameBoard)
            return json.dumps({
                "FEN": gameBoard.fen(),
                "nextPlayer": player2,
                "moveMade": playerMove,
                "isGameOver": gameOver
            })
        else:
            return json.dumps({
               "FEN": "",
               "nextPlayer": player1,
               "moveMade": playerMove,
               "isGameOver": False
            })
        
        
    
def on_request(ch, method, props, body):
    request = str(body)
    print(request)
    response = makeMove(request)

    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id=props.correlation_id),
                     body=str(response))
    
    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='rpc_queue', on_message_callback=on_request)

print(" [x] Awaiting RPC Requests")
channel.start_consuming()
