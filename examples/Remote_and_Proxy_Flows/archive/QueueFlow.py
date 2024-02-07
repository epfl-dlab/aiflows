from aiflows.base_flows import AtomicFlow,CompositeFlow
from aiflows.utils import logging
from typing import Dict, Any, List, Union
from copy import deepcopy
import hydra
import colink as CL
import pickle
from aiflows.utils import logging

log = logging.get_logger(f"aiflows.{__name__}")

def push_to_queue(data: Dict[str,Any] ,send_to: List[CL.Participant], cl: CL.CoLink):
    """ Pushes data to a colink queue. The data is sent to the participants specified in send_to.
    
    :param data: The data to be sent.
    :type data: Dict[str,Any]
    :param send_to: A list of participants to send the data to.
    :type send_to: List[CL.Participant]
    :param cl: A CoLink instance. used for putting data in participants' respective storages.
    :type cl: CL.CoLink
    """
    
    #get user ids of participants we want to send data to
    sent_to_ids = [participant.user_id for participant in send_to]
    
    #update remote storage of each participant with data
    cl.remote_storage_update(
        providers = sent_to_ids,
        key = "flow_data",
        payload = pickle.dumps(data),
        is_public = False,
    )
    
def pull_from_queue(sender: CL.Participant, subscriptions:  Union[CL.CoLinkRedisSubscriber, CL.CoLinkRabbitMQSubscriber], cl: CL.CoLink):
    """ Pulls the next update message from a colink queue of the sender and returns it.
    
    :sender: The participant whose queue we want to pull from.
    :type sender: CL.Participant
    :subscriptions: A dictionary of subscriptions. The keys are the user ids of the participants and the values are the subscriptions to their queues.
    :type subscriptions: Dict[str, Union[CL.CoLinkRedisSubscriber, CL.CoLinkRabbitMQSubscriber]]
    :param cl: A CoLink instance. Currently unused.
    :type cl: CL.CoLink
    :return: The data pulled from the queue.
    :rtype: Dict[str,Any]
    """
    
    #fetch message from queue
    message = CL.SubscriptionMessage().FromString(subscriptions[sender.user_id].get_next())
    
    #keep fetching messages until we get an update message (e.g, we don't want it to be a delete message)
    while message.change_type != "update":
        message = CL.SubscriptionMessage().FromString(subscriptions[sender.user_id].get_next())
    
    #return unpickled message payload
    return pickle.loads(message.payload)


class QueueFlow(CompositeFlow):
    def __init__(self,
                 subscriptions: Dict[str, Union[CL.CoLinkRedisSubscriber, CL.CoLinkRabbitMQSubscriber]] = {},
                 participants: List[CL.Participant] = [],
                 **kwargs):
        super().__init__(**kwargs)
        
        self.set_participants(participants)
        self.set_subscriptions(subscriptions)
        self._validate_consumer_flow()
        self.consumer_flow = self.subflows[0]
    
    def _validate_consumer_flow(self):
        """ Current implementation requires that there's exactly one subflow"""
        assert len(self.subflows) == 1, "QueueFlow must have exactly one subflow"
                
    def set_participants(self,participants: List[CL.Participant]):
        self.role_to_particiant_idx = {}
        self.participants = participants
        for i,participant in enumerate(participants):
            self.role_to_particiant_idx[participant.role] = i
            
    def set_subscriptions(self, subscriptions: Dict[str, Union[CL.CoLinkRedisSubscriber, CL.CoLinkRabbitMQSubscriber]]):
         #if we're not already subscribed to the user's queue, subscribe
         self.subscriptions = subscriptions
         
    def get_participant(self,role: str):
        return self.participants[self.role_to_particiant_idx[role]] if role in self.role_to_particiant_idx else None
                     
    def run(self, input_data: Dict[str, Any]):
        
        #Get Meta Data
        meta_data = input_data.pop("meta_data")
        action = meta_data["action"]
        
        # Case where we're pushing to a queue (FYI: Seems not possible to push to your own queue)
        if action == "push_to_queue":
            participants = [self.get_participant(participant) for participant in meta_data["participants"]]
            #TODO: Do I want to pass state ALL the time ? E.g whe I'm not pushing to a ProxyFlow
            # - If not, should I have a flag which specified whether to pass state or not ?
            # - I'll assume this for the moment
            include_state = True #TODO: Make this configurable
            input_data["state"].pop("state",None)
            if include_state:
                state = self.consumer_flow.__getstate__(ignore_proxy_info=True)
                input_data["state"] = state
                     
            try:
                push_to_queue(input_data ,send_to=participants, cl = self.cl)
                res = {"status":"success"}
                
            except Exception as e:
                log.info(f"Message not added to queue\n. Error: {e}")
                res = {"status":"failure"}
            #At the moment I need to pass a non empty dictionary. Otherwise raises error. Should we change this ?
            return res
        
        elif action == "pull_from_queue":
            #there can be only one participant in this case (one sender).
            participant = self.get_participant(meta_data["participants"][0])
            input_to_flow = pull_from_queue(sender=participant, subscriptions=self.subscriptions, cl = self.cl)
            log.debug(f"Message pulled from queue\n")
            return input_to_flow

        elif action == "call":
            
            #TODO: Do I want to pass state ALL the time ? E.g whe I'm not pushing to a ProxyFlow
            # - If not, should I have a flag which specified whether to pass state or not ?
            # - I'll assume this for the moment
            
            keep_state = False
            #pop state and flow config from input_data (if any)
            if not keep_state:
                state = input_data.pop("state", {})
                flow_config = state.get("flow_config", {})
                
                #instantiates flow from config and sets state
                self.consumer_flow = self.consumer_flow.instantiate_from_default_config(**flow_config)
                self.consumer_flow.__setflowstate__(state)
            
            #run flow on data (I'm assuming that data is in "data" field here) 
            # - TODO: Check if problematic for interfaces
            data = input_data.pop("data")
            # very ugly, is there some way to do this better ?
            msg = self._package_input_message(data,dst_flow=self.consumer_flow)
            output = self.consumer_flow(msg).data["output_data"]
            res = {"data": output}
            return res
            
        else:
            raise ValueError(f"Invalid action {action} selected")