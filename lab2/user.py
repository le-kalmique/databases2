import redis
import atexit
import datetime
import logging

logging.basicConfig(filename="messenger.log", level=logging.INFO)

def sign_in(c, username) -> int:
    user_id = c.hget("users:", username)

    if not user_id:
        print(f"No user {username}. Check the ursername or register first.")
        return -1

    c.sadd("online:", username)
    logging.info(f"{datetime.datetime.now()}\t{username}: logged in\n")
    return int(user_id)


def sign_out(c, user_id) -> int:
    username = c.hmget(f"user:{user_id}", ["login"])[0]
    logging.info(f"{datetime.datetime.now()}\t{username}: signed out\n")
    return c.srem("online:", c.hmget(f"user:{user_id}", ["login"])[0])


def create_message(c, message_text, sender_id, consumer) -> int:
    try:
        message_id = int(c.incr('message:id:'))
        consumer_id = int(c.hget("users:", consumer))
    except TypeError:
        print(f"No user {consumer}, please, try again")
        return -1

    pipeline = c.pipeline(True)
    pipeline.hmset(f'message:{message_id}', {
        'text': message_text,
        'id': message_id,
        'sender_id': sender_id,
        'consumer_id': consumer_id,
        'status': "created"
    })
    pipeline.lpush("queue:", message_id)
    pipeline.hmset(f'message:{message_id}', {
        'status': 'queue'
    })
    user = c.hmget(f"user:{sender_id}", ["login"])[0]
    pipeline.zincrby("sent:", 1, f"user:{user}")
    pipeline.hincrby(f"user:{sender_id}", "queue", 1)
    pipeline.execute()

    return message_id

def register(c, username):
    if c.hget('users:', username):
        print(f"User {username} already exists. Please, choose another username")
        return None

    user_id = c.incr('user:id:')
    pipeline = c.pipeline(True)
    pipeline.hset('users:', username, user_id)
    pipeline.hmset(f'user:{user_id}', {
        'login': username,
        'id': user_id,
        'queue': 0,
        'checking': 0,
        'blocked': 0,
        'sent': 0,
        'delivered': 0
    })
    pipeline.execute()
    logging.info(f"{datetime.datetime.now()}\t{username}: registered\n")
    return user_id

def print_messages(c, user_id):
    messages = c.smembers(f"sentto:{user_id}")
    for message_id in messages:
        message = c.hmget(f"message:{message_id}", ["sender_id", "text", "status"])
        sender_id = message[0]

        sender = c.hmget("user:%s" % sender_id, ["login"])[0]
        print(f"From {sender}:\n\t{message[1]}")
        if message[2] != "delivered":
            pipeline = c.pipeline(True)
            pipeline.hset(f"message:{message_id}", "status", "delivered")
            pipeline.hincrby(f"user:{sender_id}", "sent", -1)
            pipeline.hincrby(f"user:{sender_id}", "delivered", 1)
            pipeline.execute()


def main_menu() -> int:
    print('=-' * 20, end="=\n")
    print("Choose your action:")
    print("1. Register")
    print("2. Login")
    print("3. Exit")
    return int(input(":: "))


def user_menu() -> int:
    print('=-' * 20, end="=\n")
    print("Choose your action:")
    print("1. Log out")
    print("2. Inbox")
    print("3. Create message")
    print("4. Statistics")
    return int(input(":: "))

def is_user_signed_in(current_user_id):
    return current_user_id != -1

def user_menu_flow(c, current_user_id):
    while True:
        choice = user_menu()

        if choice == 1:
            sign_out(c, current_user_id)
            username = c.hmget("user:%s" % current_user_id, ["login"])[0]
            c.publish('users', f"User {username} signed out")
            break

        elif choice == 2:
            print_messages(c, current_user_id)

        elif choice == 3:
            try:
                message = input("Enter your message: ")
                recipient = input("To: ")
                if create_message(c, message, current_user_id, recipient):
                    print("Sending...")
            except ValueError:
                print("User doesn't exist")

        elif choice == 4:
            current_user = c.hmget(f"user:{current_user_id}", ['queue', 'checking', 'blocked', 'sent', 'delivered'])
            print("In queue: %s\nChecking: %s\nBlocked: %s\nSent: %s\nDelivered: %s".format(tuple(current_user)))


def main():

    c = redis.Redis(charset="utf-8", decode_responses=True)

    while True:
        choice = main_menu()

        if choice == 1:
            login = input("Choose a username: ")
            register(c, login)

        elif choice == 2:
            login = input("Login: ")
            current_user_id = sign_in(c, login)
            if is_user_signed_in(current_user_id):
                username = c.hmget(f"user:{current_user_id}", ["login"])[0]
                c.publish('users', f"{username} signed in")
                user_menu_flow(c, current_user_id)

        elif choice == 3:
            print("Quiting...")
            break

if __name__ == '__main__':
    main()