from flask import Flask, request
from twilio.rest import Client
import pika
import uuid
import re

app = Flask(__name__)

class MessengerClient(object):
    def __init__(self):
        account_sid = "AC7900bdb31e3ff93ca21a444346b588f4" # os.environ['TWILIO_ACCOUNT_SID']
        auth_token = "7de414004199418fce905efe092c9a19" #os.environ['TWILIO_AUTH_TOKEN']
        self.twilio_client = Client(account_sid, auth_token)

    def send_message_your_move(self , client_number, fen):
        your_move_message = "Play your next move!"
        message = self.twilio_client.messages.create(
            body=your_move_message,
            from_='+18336301344',
            media_url=['https://chessboardimage.com/{0}.png'.format(fen)],
            to=client_number
        )
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

@app.route('/sendChessMove', methods=['POST'])
def sendChessMove():
    from_num = request.form['From']
    message_body = request.form['Body']
    queueMessage ="ERROR"
    new_game_match = re.match(r"NEWGAME,(\d+),(\w+)", message_body)
    next_move = re.match(r"(\d+),(\w+)",message_body)
    if(new_game_match):
        to_num = new_game_match[1]
        first_move = new_game_match[2]
        queueMessage = f'new_game,{from_num},{to_num},{first_move}'
    elif (next_move):
        to_num = next_move[1]
        first_move = next_move[2]
        queueMessage=f'{from_num},{to_num},{first_move}'

    response = CGRC.update_queue(queueMessage)
    print(response)
    return response

if __name__ == '__main__':
    app.run()
