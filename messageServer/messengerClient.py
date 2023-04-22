from twilio.rest import Client

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
            from_='+16206791344',
            to="+1"+client_number
        )
        print(message.sid, message.body)