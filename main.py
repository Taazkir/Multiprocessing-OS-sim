import queue
import time

import psutil
import threading
import os
import signal
import multiprocessing


class ProcessManager:
    def __init__(self):
        self.processes = {}

    def update_processes(self):
        self.processes = {}
        for process in psutil.process_iter():
            self.processes[process.pid] = process

    def list_processes(self):
        self.update_processes()
        for pid, process in self.processes.items():
            # Access denied, move to next process
            try:
                process_status = process.status()
                num_threads = process.num_threads()
                thread_ids = [thread.id for thread in process.threads()]
            except psutil.AccessDenied as e:
                if pid == 0:  # Check if the process is kernel_task
                    print("Access denied for kernel_task.")
                else:
                    print(f"PID: {pid}, Name: {process.name()}, Status: {process.status()}")
                continue

            # Only proceed if access is granted
            print(
                f"PID: {pid}, Name: {process.name()}, Status: {process_status}, Threads: {num_threads}, Thread IDs: {thread_ids}")

    def create_process(self, target, args):
        process = multiprocessing.Process(target=target, args=args)
        process.start()
        self.processes[process.pid] = process
        print(f"Process created with PID {process.pid}.")
        return process.pid

    def kill_process(self, pid):
        try:
            process = self.processes[pid]
            process.kill()
            del self.processes[pid]
            print(f"Process with PID {pid} has been terminated.")
        except KeyError:
            print(f"No process found with PID {pid}.")
        except psutil.NoSuchProcess:
            print(f"No process found with PID {pid}.")
        except psutil.AccessDenied:
            print(f"Access denied to process with PID {pid}.")

    def suspend_process(self, pid):
        try:
            process = psutil.Process(pid)
            process.suspend()
            print(f"Process with PID {pid} suspended successfully.")
        except psutil.NoSuchProcess:
            print(f"No process found with PID {pid}.")
        except psutil.AccessDenied:
            print(f"Access denied to process with PID {pid}.")

    def resume_process(self, pid):
        try:
            process = psutil.Process(pid)
            process.resume()
            print(f"Process with PID {pid} resumed successfully.")
        except psutil.NoSuchProcess:
            print(f"No process found with PID {pid}.")
        except psutil.AccessDenied:
            print(f"Access denied to process with PID {pid}.")

    def send_message(self, conn, message):
        try:
            for msg in message:
                conn.send(msg)
                print(f"Message sent: {msg}")
            conn.close()
        except BrokenPipeError:
            print("Connection closed.")

    def receive_message(self, conn):
        while True:
            try:
                msg = conn.recv()
                if msg == "END":
                    break
                print("Received the message: {}".format(msg))
            except EOFError:
                print("Connection closed.")
                break


class ThreadManager:
    def __init__(self):
        self.threads = {}
    def update_threads(self):
        self.threads = {}
        for thread in threading.enumerate():
            self.threads[thread.ident] = thread

    def list_threads(self):
        self.update_threads()
        for thread_id, thread in self.threads.items():
            print(f"Thread ID: {thread.ident}, Name: {thread.name}, Status: {thread.is_alive()}")

    def create_thread(self, target, args):
        thread = threading.Thread(target=target, args=args)
        thread.start()
        self.threads[thread.ident] = thread
        print(f"Thread created with ID {thread.ident}.")
        return thread.ident

    def kill_thread(self, thread_id):
        try:
            thread = self.threads[thread_id]
            thread.join(timeout=0)  # Ensure the thread is not alive
            del self.threads[thread_id]
            print(f"Thread with ID {thread_id} has been terminated.")
        except KeyError:
            print(f"No thread found with ID {thread_id}.")
        except AttributeError:
            print(f"Thread with ID {thread_id} does not support termination.")

    def suspend_thread(self, thread_id):
        try:
            thread = self.threads[thread_id]
            thread.suspend()  # Suspend the thread
            print(f"Thread with ID {thread_id} suspended successfully.")
        except KeyError:
            print(f"No thread found with ID {thread_id}.")
        except AttributeError:
            print(f"Thread with ID {thread_id} does not support suspending.")

    def resume_thread(self, thread_id):
        try:
            thread = self.threads[thread_id]
            thread.resume()  # Resume the thread
            print(f"Thread with ID {thread_id} resumed successfully.")
        except KeyError:
            print(f"No thread found with ID {thread_id}.")
        except AttributeError:
            print(f"Thread with ID {thread_id} does not support resuming.")

    def producer(self, queue,  consumer_tid, message):
        producer_tid = threading.get_ident()
        for msg in message:
            queue.put((producer_tid, consumer_tid, msg))
            print(f"Message sent: \"{msg}\" from thread {producer_tid} to thread {consumer_tid}")

    def consumer(self, queue):
        while True:
            producer_id, consumer_id, msg = queue.get()
            if msg == "END":
                break
            print(f"Message from thread {producer_id} to thread {consumer_id}: {msg}")


# Function to simulate IPC with shared memory
def square_numbers(allist, results, square_sum):
    for i, number in enumerate(allist):
        results[i] = (number ** 2)
    square_sum.value = sum(results)
    # print result Array
    print("Result(in process p1): {}".format(results[:]))

    # print square_sum Value
    print("Sum of squares(in process p1): {}".format(square_sum.value))


# Function to simulate thread communication
def thread_task(shared_data, message_queue):
    for i in range(10):
        with shared_data.get_lock():
            shared_data[0] += 1
        message_queue.put(i)
    # print result Array
    print("Shared data(in new thread): {}".format(shared_data[:]))
    print("Message Queue(in new thread): {}".format(list(message_queue.queue)))

# Function to simulate creating a new thread
def new_thread():
    print("New thread created.")
    time.sleep(25)
    print("New thread finished.")

# Function to simulate creating a new process
def new_process():
    print("New process created.")
    time.sleep(30)
    print("New process finished.")


def main():
    process_manager = ProcessManager()
    thread_manager = ThreadManager()

    while True:
        print("\n1. List Processes")
        print("2. List Threads")
        print("3. Create Process")
        print("4. Suspend Process")
        print("5. Resume Process")
        print("6. Kill Process")
        print("7. Create Thread")
        print("8. Suspend Thread")
        print("9. Resume Thread")
        print("10. Kill Thread")
        print("11. Send Message between Threads via message passing")
        print("12. Send Message between Threads via shared memory")
        print("13. Send Message between Processes via Pipe")
        print("14. Send Message between Processes via shared memory")
        print("15. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            process_manager.list_processes()

        elif choice == '2':
            thread_manager.list_threads()

        elif choice == '3':
            process_manager.create_process(new_process, ())

        elif choice == '4':
            pid = int(input("Enter PID of process to suspend: "))
            process_manager.suspend_process(pid)

        elif choice == '5':
            pid = int(input("Enter PID of process to resume: "))
            process_manager.resume_process(pid)

        elif choice == '6':
            pid = int(input("Enter PID of process to kill: "))
            process_manager.kill_process(pid)

        elif choice == '7':
            thread_manager.create_thread(new_thread, ())

        elif choice == '8':
            thread_id = int(input("Enter ID of thread to suspend: "))
            thread_manager.suspend_thread(thread_id)

        elif choice == '9':
            thread_id = int(input("Enter ID of thread to resume: "))
            thread_manager.resume_thread(thread_id)

        elif choice == '10':
            thread_id = int(input("Enter ID of thread to kill: "))
            thread_manager.kill_thread(thread_id)

        elif choice == '11':
            message_queue = queue.Queue()
            message = input("Enter message to send: ")
            msgs = message.split(' ')
            msgs.append("END")
            t1 = threading.Thread(target=thread_manager.consumer, args=(message_queue,))
            t1_id = threading.get_ident()
            t2 = threading.Thread(target=thread_manager.producer, args=(message_queue, t1_id, msgs))
            t2.start()
            t1.start()
            t2.join()
            t1.join()

        elif choice == '12':
            shared_data = multiprocessing.Array('i', [0])
            message_queue = queue.Queue()
            # creating new thread
            t1 = threading.Thread(target=thread_task, args=(shared_data, message_queue,))
            t1.start()
            t1.join()
            # print result Array
            print("Shared data(in main thread): {}".format(shared_data[:]))
            print("Message Queue(in main thread): {}".format(list(message_queue.queue)))

        elif choice == '13':
            message = input("Enter message to send: ")
            msgs = message.split(' ')
            msgs.append("END")
            # creating a pipe
            parent_conn, child_conn = multiprocessing.Pipe()
            # creating new processes
            p1 = multiprocessing.Process(target=process_manager.send_message, args=(parent_conn, msgs))
            p2 = multiprocessing.Process(target=process_manager.receive_message, args=(child_conn,))
            # running processes
            p1.start()
            p2.start()
            # wait until processes finish
            p1.join()
            p2.join()

        elif choice == '14':
            allist = [1, 2, 3, 4, 5]
            # creating shared memory
            results = multiprocessing.Array('i', len(allist))
            square_sum = multiprocessing.Value('i')
            # creating new process
            p1 = multiprocessing.Process(target=square_numbers, args=(allist, results, square_sum))
            p1.start()
            p1.join()
            # print result array
            print("Result(in main program): {}".format(results[:]))
            # print square_sum Value
            print("Sum of squares(in main program): {}".format(square_sum.value))

        elif choice == '15':
            break

        else:
            print("Invalid choice. Please try again.")

    print("Exiting program.")


if __name__ == "__main__":
    main()
