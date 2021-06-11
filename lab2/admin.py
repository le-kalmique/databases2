import redis

def admin_menu():
    print('=-' * 20, end="=\n")
    print("\t\tAdmin")
    print("Choose your action:")
    print("1. Users online")
    print("2. Top senders")
    print("3. Top spamers")
    print("0. Exit")
    return int(input(":: "))

def main():
    loop = True
    connection = redis.Redis(charset="utf-8", decode_responses=True)

    while loop:
        choice = admin_menu()

        if choice == 1:
            online_users = connection.smembers("online:")
            print('=-' * 20, end="=\n")
            print("\t\tOnline")
            for user in online_users:
                print(user)

        elif choice == 2:
            top_senders_count = 5
            senders = connection.zrange("sent:", 0, top_senders_count, desc=True, withscores=True)
            
            print('=-' * 20, end="=\n")
            print(f"Top-{top_senders_count} senders")
            for index, sender in enumerate(senders):
                print(f"{index + 1}. {sender[0]}:\t{int(sender[1])} message(s)")

        elif choice == 3:
            top_spamers_count = 5
            spamers = connection.zrange("spam:", 0, top_spamers_count, desc=True, withscores=True)
            print('=-' * 20, end="=\n")
            print(f"Top-{top_spamers_count} spamers")
            for index, spamer in enumerate(spamers):
                print(f"{index + 1}. {spamer[0]}:\t{int(spamer[1])} spam message(s)")

        elif choice == 0:
            print("Quiting...")
            loop = False


if __name__ == '__main__':
    main()
