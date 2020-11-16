# Changelog

## 0.3.7

* use try/finally block to close session, race condition? Not reproducible.

## 0.3.6

* explicitly close session when we create it

## 0.3.5

* work around misbehaving upstream proxy by adding keep-alive header

## 0.3.4

* nicer log output in pipeline based on stage name

## 0.3.2

* Python 3.8 changes how functools.partial() wraps async functions, needed
  a minor patch

## 0.3.1

* read response.body instead of response.text to allow downloading of binary files
* track_urls is now True by default

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
