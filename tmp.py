import dramatiq
import requests
from dramatiq.brokers.redis import RedisBroker

redis_broker = RedisBroker(host="localhost", port=6379)
dramatiq.set_broker(redis_broker)


@dramatiq.actor
def count_words(url):
    response = requests.get(url)
    count = len(response.text.split(" "))
    print(f"There are {count} words at {url!r}.")


if __name__ == '__main__':

    # Synchronously count the words on example.com in the current process
    # count_words("https://google.com")

    # or send the actor a message so that it may perform the count
    # later, in a separate process.
    count_words.send("https://facebook.com")
