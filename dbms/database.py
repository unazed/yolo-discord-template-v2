import os
import json
import time, inspect


_print = print
def print(*args, **kwargs): 
    prev_fn = inspect.currentframe().f_back.f_code.co_name
    _print(f"[{time.strftime('%H:%M:%S')}] [DatabaseProcess] [{prev_fn}]",
           *args, **kwargs)


def save_database(database, path_to_db):
    with open(path_to_db, 'w') as save:
        json.dump(database, save, indent=4)


def poll_indefinitely(master_pipe, path_to_db):
    if not os.path.isfile(path_to_db):
        with open(path_to_db, 'w') as _:
            pass
    with open(path_to_db) as database:
        try:
            database = json.load(database)
        except json.JSONDecodeError:
            return master_pipe.send({
                "error": True,
                "message": "failed to load database"
                })
    master_pipe.send({
        "error": False,
        "message": "loaded database"
        })

    default_poll_timeout    = 1
    default_save_interval   = 60 * 60
    default_daily_interval  = 60 * 60 * 24
    default_daily_increment = 50

    last_save_timestamp = time.time()

    while True:
        try:
            if not master_pipe.poll(default_poll_timeout):
                if time.time() - last_save_timestamp >= default_save_interval:
                    print(f"saving database with {len(database)} user(s)")
                    save_database(database, path_to_db)
                    last_save_timestamp = time.time()
                continue

            message = master_pipe.recv()

            if message['event'] == "update":
                print("populating user database")
                for uid, user_info in message['data'].items():
                    uid = str(uid)
                    if uid not in database:
                        database[uid] = {}
                    database[uid].update({
                            "username": user_info['username'],
                            "balance": database.get(uid, {}).get("balance", 50),
                            "last-daily": database.get(uid, {}).get("last-daily", 0),
                            "vouches": 0
                            })
            elif message['event'] == "daily":
                if (user := database.get(str(message['uid']), None)) is None:
                    master_pipe.send({
                        "error": True,
                        "action": "do-update"
                        })
                elif (diff := time.time() - user['last-daily']) <= default_daily_interval:
                    master_pipe.send({
                        "error": True,
                        "try-after": (default_daily_interval - diff)/(60 * 60)
                        })
                else:
                    user['last-daily'] = time.time()
                    user['balance'] += default_daily_increment

                    if 10000 <= user['balance'] < 25000:
                        master_pipe.send({
                            "error": False,
                            "upgrade": 1
                            })
                    elif 25000 <= user['balance']:
                        master_pipe.send({
                            "error": False,
                            "upgrade": 2
                            })
                    else:    
                        master_pipe.send({"error": False})
            elif message['event'] == "query":
                if (user := database.get(str(message['uid']), None)) is None:
                    master_pipe.send({
                        "error": True,
                        "action": "do-update"
                        })
                else:
                    master_pipe.send({"error": False, "data": user})
            elif message['event'] == "give-money":
                if (user := database.get(str(message['uid']), None)) is None:
                    master_pipe.send({
                        "error": True,
                        "action": "do-update"
                        })
                else:
                    database[str(message['uid'])]['balance'] += message['amount']
            elif message['event'] == "add-vouch":
                if (user := database.get(str(message['uid']), None)) is None:
                    master_pipe.send({
                        "error": True,
                        "action": "do-update"
                        })
                else:
                    database[str(message['uid'])]['vouches'] += message['amount']
        except (KeyboardInterrupt, EOFError):
            print("closing")
            break

