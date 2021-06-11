import time
import random
from threading import Thread
from messagelistener import EventListener

import redis

class QueueMessageWorker(Thread):

    def __init__(self, conn, delay):
        Thread.__init__(self)
        self.conn = conn
        self.delay = delay

    def run(self):
        while True:
            message = self.conn.brpop("queue:")
            if message:
                message_id = int(message[1])

                self.conn.hmset(f'message:{message_id}', {
                    'status': 'checking'
                })
                message = self.conn.hmget(f"message:{message_id}", ["sender_id", "consumer_id"])
                sender_id = int(message[0])
                consumer_id = int(message[1])
                self.conn.hincrby(f"user:{sender_id}", "queue", -1)
                self.conn.hincrby(f"user:{sender_id}", "checking", 1)
                time.sleep(self.delay)

                message_text = self.conn.hmget(f"message:{message_id}", ["text"])[0]
                is_spam = "spam" in message_text
                pipeline = self.conn.pipeline(True)
                pipeline.hincrby(f"user:{sender_id}", "checking", -1)
                if is_spam:
                    print(f"{message_id} msg BLOCKED for spam")
                    sender_username = self.conn.hmget(f"user:{sender_id}", ["login"])[0]
                    pipeline.zincrby("spam:", 1, f"user:{sender_username}")
                    pipeline.hmset(f'message:{message_id}', {
                        'status': 'blocked'
                    })
                    pipeline.hincrby(f"user:{sender_id}", "blocked", 1)
                    pipeline.publish('spam', f"User {sender_username} sent spam message: \"{message_text}\"")
                else:
                    print(f"{message_id} msg SENT")
                    pipeline.hmset(f'message:{message_id}', {
                        'status': 'sent'
                    })
                    pipeline.hincrby(f"user:{sender_id}", "sent", 1)
                    pipeline.sadd(f"sentto:{consumer_id}", message_id)
                pipeline.execute()


def main():
    handlers_count = 5
    connection = redis.Redis(charset="utf-8", decode_responses=True)
    listener = EventListener(connection)
    listener.setDaemon(True)
    listener.start()
    for x in range(handlers_count):
        connection = redis.Redis(charset="utf-8", decode_responses=True)
        worker = QueueMessageWorker(connection, random.randint(0, 3))
        worker.daemon = True
        worker.start()
    while True:
        pass

if __name__ == '__main__':
    main()