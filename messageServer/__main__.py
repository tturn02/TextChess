from flask import Flask, request
import re
import json
from messengerClient import MessengerClient
from queueClient import ChessGameRequestClient

CGRC = ChessGameRequestClient()
Messenger = MessengerClient()

app = Flask(__name__)

def process_message_body( message ):
    message = message.replace(" ","")
    message = message.upper()
    new_game_match = re.match(r"NEWGAME:(\d+),(\w+#?)", return_message)
    next_move_match = re.match(r"MOVE:(\d+),(\w+#?)",message_body)

    if(new_game_match):
        player_num = new_game_match[1]
        first_move = new_game_match[2]
        return f'new_game,{from_num},{to_num},{first_move}'
    if(next_move_match):
        player_num = next_move_match[1]
        next_move = next_move_match[2]
        return f'{from_num},{to_num},{first_move}'
    
    return None


@app.route('/sendChessMove', methods=['POST'])
def sendChessMove(): 
    from_num = request.form['From'][2:]
    message_body = request.form['Body']
    queueMessage = process_message_body(message_body)

    if(queueMessage != None):
        response = CGRC.update_queue(queueMessage)
        data = json.loads(response.decode("utf-8"))
        if(data['FEN'] != ""):
            if(data['isGameOver'] == True):
                Messenger.send_message_gameover(data['nextPlayer'])
            else: 
                Messenger.send_message_your_move(data['nextPlayer'],data['FEN'],data['moveMade'])

        return response

    return "ERROR"

if __name__ == '__main__':
    app.run()
