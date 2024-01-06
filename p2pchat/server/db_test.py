from server_db import ServerDB, SQLiteConnectionPool
import threading, time
import datetime
import matplotlib.pyplot as plt

# demo
if __name__ == "__main__":
    db = ServerDB(100)

    x = []
    y = []
    for i in range(1, 1000, 10):
        threads = []
        for _ in range(i):
            t = threading.Thread(target=db.get_chatroom_members, args=("bb",))
            threads.append(t)
        start_time = time.time()
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # End time
        end_time = time.time()
        elapsed_time_millis = (end_time - start_time) * 1000
        print(f"Elapsed time for {i} threads: {elapsed_time_millis:.2f} milliseconds")
        x.append(i)
        y.append(elapsed_time_millis)
    plt.semilogx(x, y)
    plt.show()
