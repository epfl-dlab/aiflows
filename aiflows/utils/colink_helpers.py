import colink as CL
import pickle

def get_next_update_message(subscriber):
    message = CL.SubscriptionMessage().FromString(
        subscriber.get_next()
    )

    while message.change_type != "update":
        message = CL.SubscriptionMessage().FromString(
            subscriber.get_next()
        )

    return pickle.loads(message.payload)


def create_subscriber(cl,response_queue_name):
    response_queue = cl.subscribe(response_queue_name, None)
                
    return cl.new_subscriber(response_queue)