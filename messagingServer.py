from flask import Flask, request
import re
import json

app = Flask(__name__)


CGRC = ChessGameRequestClient()
Messenger = MessengerClient()
@app.route('/sendChessMove', methods=['POST'])
def sendChessMove(): 

    from_num = request.form['From'][2:]
    message_body = request.form['Body']
    print("Message BODY:", message_body)
    queueMessage ="ERROR"

    message_body = message_body.replace(" ", "")
    new_game_match = re.match(r"NEWGAME:(\d+),(\w+)", message_body)
    next_move = re.match(r"MOVE:(\d+),(\w+)",message_body)

    if(new_game_match):
        to_num = new_game_match[1]
        first_move = new_game_match[2]
        queueMessage = f'new_game,{from_num},{to_num},{first_move}'
    elif (next_move):
        to_num = next_move[1]
        first_move = next_move[2]
        queueMessage=f'{from_num},{to_num},{first_move}'

    print("queue message:", queueMessage)
    if(queueMessage != "ERROR"):
        response = CGRC.update_queue(queueMessage)

        data = json.loads(response.decode("utf-8"))
        if(data['isGameOver'] == True):
            Messenger.send_message_gameover(data['nextPlayer'])
        else: 
            Messenger.send_message_your_move(data['nextPlayer'],data['FEN'],data['moveMade'])

        return response

    return "none"

if __name__ == '__main__':
    app.run()
