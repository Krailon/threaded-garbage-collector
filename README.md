# threaded-garbage-collector
A Python 3.6 multi-threaded garbage collector example with optional reactive garbage collection wrapped in a convenient command shell

```
> help

Documented commands (type help <topic>):
========================================
EOF  close  collector  exit  garbage  help  pool  quit

> help pool
pool - print data pool contents

> help garbage
garbage [lifetime] - Adds random garbage data with optional lifetime (defaults to random in [1, 240] seconds)

> help delete
delete id - delete data from the pool

> help collector
collector start|stop|enable|disable
    Start/stop periodic garbage collector thread or enable/disable reactive garbage collection.
    Reactive collection is activated upon addition of new data.
```
