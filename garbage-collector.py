#!/usr/bin/env python3.6
#
# Multi-Threaded Garbage Collection Example by NOP-Gate/StackCanary
#
from random import randint
from datetime import datetime as dt
from time import sleep
from uuid import uuid4
from cmd import Cmd
from threading import Thread, Lock


COLLECTOR_PERIOD = 30  # Seconds
LOG_NAME = 'garbage-collector.log'


pool = {}
pool_lock = Lock()
sleep_lock = Lock()
stop_collecting = False

# Open the log file
log = open(LOG_NAME, 'w')
log.write('\nThreaded Garbage Collector Example Started')
print(F'Opened log file "{LOG_NAME}" - tail it for garbage collector thread output (tail -f {LOG_NAME})')


class GarbageConsole(Cmd):
    intro = F'Multi-Threaded Garbage Collection Example\n\n{Cmd.do_help.__code__.co_consts[0]}'
    prompt = '> '
    collector = None
    reactive_collection = False  # Reactive collection is activated upon addition of new data

    def default(self, line):
        print(F'Error: "{line}" is not a valid command')

    def emptyline(self):
        pass

    def do_collector(self, action):
        """collector start|stop|enable|disable
    Start/stop periodic garbage collector thread or enable/disable reactive garbage collection.
    Reactive collection is activated upon addition of new data.
        """
        action = action.lower()
        if action == 'start':
            if self.collector is not None:
                print('Collector is already running')
                return

            try:
                log_message(F'Starting garbage collector with {COLLECTOR_PERIOD}s period...', True)
                self.collector = Thread(target=garbage_collector)
                self.collector.start()
            except Exception as ex:
                print(F'Error: {str(ex)}')
        elif action == 'stop':
            if self.collector is None:
                print('Collector is not running')
                return

            log_message('Stopping garbage collector...', True)
            global stop_collecting
            stop_collecting = True
            sleep_lock.release()
        elif action == 'enable':
            self.reactive_collection = True
            log_message('Reactive garbage collection enabled', True)
        elif action == 'disable':
            self.reactive_collection = False
            log_message('Reactive garbage collection disabled', True)
        elif action == '':
            print('Error: an action is required (one of: start/stop/enable/disable)')
        else:
            print(F'Error: "{action}" is not a valid collector action (valid actions: start/stop/enable/disable)')

    def do_pool(self, _):
        """pool - print data pool contents"""
        print('Data:')
        pool_lock.acquire()

        for id in pool:
            print(F'  {id} - {pool[id]} (age: {(dt.now() - pool[id]["created"]).total_seconds()}s)')

        pool_lock.release()

    def do_delete(self, id):
        """delete id - delete data from the pool"""
        if id == '':
            print('Error: you must specify the id of the data to be deleted')
            return
        elif id not in pool:
            print(F'Error: no data with id "{id}" found in the pool')
            return

        pool_lock.acquire()
        del pool[id]
        pool_lock.release()

        log_message(F'Deleted data "{id}"', True)

    def do_garbage(self, lifetime):
        """garbage [lifetime] - Adds random garbage data with optional lifetime (defaults to random in [1, 240] seconds)"""
        if lifetime == '':
            lifetime = randint(1, 241)

        pool_lock.acquire()

        id = uuid4().hex
        pool[id] = {
            'data': None,  # Data would go here, obviously
            'created': dt.now(),  # Consider using most recent access time instead
            'lifetime': int(lifetime)
        }

        log_message(F'Added garbage data "{id}" with lifetime {lifetime}s', True)
        pool_lock.release()

        # Activate reactive garbage collection if enabled
        if self.reactive_collection is True:
            collector_thread = Thread(target=garbage_collector, args=(True,))
            collector_thread.start()

    def do_EOF(self, _):
        """Exit with CTRL+D"""
        return self.do_exit()

    def do_quit(self, _):
        """Exit"""
        return self.do_exit()

    def do_close(self, _):
        """Exit"""
        return self.do_exit()

    def do_exit(self, _=None):
        """Exit"""
        # Signal collector thread to exit and release its sleep lock to wake it up
        if self.collector is not None:
            global stop_collecting
            stop_collecting = True
            sleep_lock.release()

        # Close log file
        log_message('Closing...')
        log.close()

        print()
        return True


def log_message(message, also_print=False):
    log.write(F'[{dt.now()}] {message}\n')
    log.flush()

    if also_print:
        print(message)


def garbage_collector(reactive=False):
    while True:
        if reactive:
            log_message('Running reactive garbage collection...')
        else:
            log_message('Running periodic garbage collection...')

        # Loop over keys indirectly or Python will scold us with exceptions
        ids = list(pool.keys())

        for id in ids:
            # Acquire lock before accessing object
            pool_lock.acquire()

            object = pool[id]
            if (dt.now() - object['created']).total_seconds() > object['lifetime']:
                del pool[id]
                log_message(F'Removed expired object "{id}"')

            pool_lock.release()

        if reactive:
            break
        else:
            # Use timeout with Lock.acquire(timeout) to control sleep duration
            # but still allow main thread to wake this thread up on exit
            sleep_lock.acquire(timeout=COLLECTOR_PERIOD)

            if stop_collecting:
                break

    if not reactive:
        try:
            # Main thread closes file handle before collector thread gets here
            # so we ignore its failure to print its dying message
            log_message('Garbage collector stopped')
        except ValueError:
            pass


def main():
    # Acquire the collector's sleep lock so we can wake it up on exit by releasing it
    sleep_lock.acquire()

    GarbageConsole().cmdloop()


if __name__ == '__main__':
    main()
