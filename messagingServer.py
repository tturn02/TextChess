from flask import Flask, request
from twilio.rest import Client
import pika
import uuid
import re
import json

app = Flask(__name__)

class MessengerClient(object):
    def __init__(self):
        account_sid ="" # os.environ['TWILIO_ACCOUNT_SID']
        auth_token = "" #os.environ['TWILIO_AUTH_TOKEN']

        self.twilio_client = Client(account_sid, auth_token)

    def send_message_your_move(self , client_number, fen, lastMove):
        #fen = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq e6 0 2"
        board = fen.split(" ")[0].replace("/","")
        print(board)
        # active_color = match.group(3)
        # castling_availability = match.group(4)
        # en_passant_square = match.group(5)
        # halfmove_clock = match.group(6)
        # fullmove_number = match.group(7)
        your_move_message = f"Your opponent played: {lastMove}\n Your turn!"
        message = self.twilio_client.messages.create(
            body=your_move_message,
            from_='+16206791344',
            media_url=['https://chessboardimage.com/{0}.png'.format(board.replace("/",""))],
            to="+1"+client_number
        )
        
        print(message.sid, message.body)

    def send_message_gameover(self, client_number):
        your_move_message = "Game Over!"
        message = self.twilio_client.messages.create(
            body=your_move_message,
            from_='+18336301344',
            media_url=['https://chessboardimage.com/{0}.png'.format(board.replace("/",""))],
            to="+1"+client_number
        )
        print(message.sid, message.body)

class ChessGameRequestClient(object):
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost')
        )

        self.channel = self.connection.channel()
        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True
        )

        self.response = None
        self.corr_id = None
    
    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body
    
    def update_queue(self, message_body):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='rpc_queue',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=str(message_body)
        )
        self.connection.process_data_events(time_limit=None)
        return self.response

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
