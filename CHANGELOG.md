# Changelog

## 0.3

* lots of refactoring
* now enqueue Requests instead of urls
* Request can now hold a callback, useful for Requests emitted by parse()
* callback can be a coro instead of only an async generator
* Spider can now track urls so the same page isn't hit twice
* page spidering is more concurrent, results are still in order
* all tests use mock requests, found and filed a bug in aiohttp (#4684)
* client_factory is now just a client object again

## 0.2

* use a Queue to hold urls
* move pipeline functionality into its own class
* use a client_factory to create ClientSession

## 0.1.2

* did I really call it DropItemBad? DropItemError

## 0.1.1

* adding DropItemBad, change logging levels

## 0.1

* initial release, seems to work
