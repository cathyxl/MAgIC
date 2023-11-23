from typing import List
import os
import re
import logging
import time
from tenacity import retry, stop_after_attempt, wait_random_exponential

from .base import IntelligenceBackend
from ..message import Message, SYSTEM_NAME, MODERATOR_NAME
from ..chatbox_config import global_config


try:
    import openai
except ImportError:
    is_openai_available = False
    # logging.warning("openai package is not installed")
else:
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    if openai.api_key is None:
        # logging.warning("OpenAI API key is not set. Please set the environment variable OPENAI_API_KEY")
        is_openai_available = False
    else:
        is_openai_available = True
        
global chatbox_function

# Default config follows the OpenAI playground
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 1070
# DEFAULT_MODEL = "gpt-3.5-turbo"
DEFAULT_MODEL = "gpt-4"

END_OF_MESSAGE = "<EOS>"  # End of message token specified by us not OpenAI
STOP = ("<|endoftext|>", END_OF_MESSAGE)  # End of sentence token
BASE_PROMPT = f"The messages always end with the token {END_OF_MESSAGE}."


class OpenAIChat(IntelligenceBackend):
    """
    Interface to the ChatGPT style model with system, user, assistant roles separation
    """
    stateful = False
    type_name = "openai-chat"

    def __init__(self, temperature: float = DEFAULT_TEMPERATURE, max_tokens: int = DEFAULT_MAX_TOKENS,
                 model: str = DEFAULT_MODEL, merge_other_agents_as_one_user: bool = True, **kwargs):
        """
        instantiate the OpenAIChat backend
        args:
            temperature: the temperature of the sampling
            max_tokens: the maximum number of tokens to sample
            model: the model to use
            merge_other_agents_as_one_user: whether to merge messages from other agents as one user message
        """
        assert is_openai_available, "openai package is not installed or the API key is not set"
        super().__init__(temperature=temperature, max_tokens=max_tokens, model=model,
                         merge_other_agents_as_one_user=merge_other_agents_as_one_user, **kwargs)

        self.temperature = temperature
        self.max_tokens = max_tokens
        self.model = model
        print("init backend", self.model, self.temperature)
        self.merge_other_agent_as_user = merge_other_agents_as_one_user

    @retry(stop=stop_after_attempt(6), wait=wait_random_exponential(min=1, max=60))
    def _get_response(self, messages):
        # print("now requesting: ", self.model)
        
        if self.model == 'gpt-3.5-turbo' or self.model == 'gpt-4':
            #time.sleep(3)
            try:
                #print(messages)
                time.sleep(4)
                completion = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stop=STOP
                )
                #print('!!!!!!!')
                #print(response)
                response = completion.choices[0]['message']['content']
                response = response.strip()
            except Exception as E:
                print(E)
                print('@@@@@@@@@@@@@@@@@@@')
        else:
            flag = True
            count = 0
            while flag:
                try:
                    time.sleep(3)
                    print('here')
                    completion = global_config.chatbox(
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                    )
                    flag = False
                    print(completion)
                    response = completion
                except Exception as E:
                    print(E)
                    print('*****************')
                    count +=1
                if count > 4:
                    flag = False

            response = response.strip()
        #print(response)
        #print('fail to response !!!!!!!!!!!\n\n')
        return response

    def query(self, agent_name: str, role_desc: str, history_messages: List[Message], global_prompt: str = None,
              request_msg=None, single_history=False, *args, **kwargs) -> str:
        """
        format the input and call the ChatGPT/GPT-4 API
        args:
            agent_name: the name of the agent
            role_desc: the description of the role of the agent
            env_desc: the description of the environment
            history_messages: the history of the conversation, or the observation for the agent
            request_msg: the request from the system to guide the agent's next response
        """
        if single_history:
            messages = [{"role": "user", "content": request_msg}]
        else:


            # Merge the role description and the global prompt as the system prompt for the agent
            if global_prompt:  # Prepend the global prompt if it exists
                system_prompt = f"{global_prompt.strip()}\n{BASE_PROMPT}\n\nYour name: {agent_name}\n\nYour role: {role_desc}"
            else:
                system_prompt = f"You are {agent_name}.\n\nYour role:{role_desc}\n\n{BASE_PROMPT}"
            

            all_messages = [(SYSTEM_NAME, system_prompt)]
            for msg in history_messages:
                if msg.agent_name == SYSTEM_NAME:
                    all_messages.append((SYSTEM_NAME, msg.content))
                else:  # non-system messages are suffixed with the end of message token
                    all_messages.append((msg.agent_name, f"{msg.content}{END_OF_MESSAGE}"))
            
            # print("request_msg", request_msg)
            if request_msg:
                if isinstance(request_msg, Message):
                    all_messages.append((SYSTEM_NAME, request_msg.content))
                elif isinstance(request_msg, str):
                    all_messages.append((SYSTEM_NAME, request_msg))
                else:
                    print("request msg type not supported, ", type(request_msg))
                
            else:  # The default request message that reminds the agent its role and instruct it to speak
                all_messages.append((SYSTEM_NAME, f"Now you speak, {agent_name}.{END_OF_MESSAGE}"))
            
            messages = []
            for i, msg in enumerate(all_messages):
                if i == 0:
                    assert msg[0] == SYSTEM_NAME  # The first message should be from the system
                    messages.append({"role": "system", "content": msg[1]})
                else:
                    if msg[0] == agent_name:
                        messages.append({"role": "assistant", "content": msg[1]})
                    else:
                        if messages[-1]["role"] == "user":  # last message is from user
                            if self.merge_other_agent_as_user:
                                messages[-1]["content"] = f"{messages[-1]['content']}\n\n[{msg[0]}]: {msg[1]}"
                            else:
                                messages.append({"role": "user", "content": f"[{msg[0]}]: {msg[1]}"})
                        elif messages[-1]["role"] == "assistant":  # consecutive assistant messages
                            # Merge the assistant messages
                            # messages[-1]["content"] = f"{messages[-1]['content']}\n{msg[1]}"
                            messages.append({"role": "user", "content": f"[{msg[0]}]: {msg[1]}"})
                        elif messages[-1]["role"] == "system":
                            messages.append({"role": "user", "content": f"[{msg[0]}]: {msg[1]}"})
                        else:
                            raise ValueError(f"Invalid role: {messages[-1]['role']}")
        #print("======current history========: ", agent_name)
        #if agent_name.startswith("Player"):
        ## if agent_name == "Player 3":
        #    for msg in messages:
        #        if msg["role"] == "system":
        #            continue
        #        print("===msg of===", msg["role"])
        #        print(msg["content"].replace("\n\n","\n"))
        

        response = self._get_response(messages, *args, **kwargs)
        # response="+++++++placeholder+++++++"
        #print("response: ", response)

        # Remove the agent name if the response starts with it
        response = re.sub(rf"^\s*\[.*]:", "", response).strip()
        response = re.sub(rf"^\s*{re.escape(agent_name)}\s*:", "", response).strip()

        # Remove the tailing end of message token
        response = re.sub(rf"{END_OF_MESSAGE}$", "", response).strip()

        return response
