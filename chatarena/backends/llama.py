from typing import List
import os
import re
import logging
from tenacity import retry, stop_after_attempt, wait_random_exponential

from .base import IntelligenceBackend
from ..message import Message, SYSTEM_NAME, MODERATOR_NAME

import requests

def send_message_llama(prompt, url='http://127.0.0.1:5000'):
    # print(prompt)
    prompt_dict = {'prompt': prompt}
    r = requests.post(f"{url}/generate", data=prompt_dict)
    res = json.loads(r.text)

    # print("prompt_part: ", res["prompt_part"])
    return res["output_code"]

# Default config follows the OpenAI playground
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 1070
# DEFAULT_MODEL = "gpt-3.5-turbo"
DEFAULT_MODEL = "gpt-4"

END_OF_MESSAGE = "<EOS>"  # End of message token specified by us not OpenAI
STOP = ("<|endoftext|>", END_OF_MESSAGE)  # End of sentence token
BASE_PROMPT = f"The messages always end with the token {END_OF_MESSAGE}."


class Llama(IntelligenceBackend):
    """
    Interface to the ChatGPT style model with system, user, assistant roles separation
    """
    stateful = False
    type_name = "llama"

    def __init__(self, temperature: float = DEFAULT_TEMPERATURE, max_tokens: int = DEFAULT_MAX_TOKENS,
                 model: str = DEFAULT_MODEL, merge_other_agents_as_one_user: bool = True, **kwargs):
        super().__init__(temperature=temperature, max_tokens=max_tokens, model=model,
                         merge_other_agents_as_one_user=merge_other_agents_as_one_user, **kwargs)

        self.temperature = temperature
        self.max_tokens = max_tokens
        self.model = model
        print("init backend", self.model, self.temperature)
        self.merge_other_agent_as_user = merge_other_agents_as_one_user

    @retry(stop=stop_after_attempt(6), wait=wait_random_exponential(min=1, max=60))
    def _get_response(self, messages):
        print("in llama now requesting: ", self.model)
        print(self.max_tokens, self.temperature)
        prompt = ""
        for item in messages:
            pre = ""
            if item["role"] == "user":
                pre = "<human>"
            elif item["role"] == "system":
                pre="<system>"
            elif item["role"] == "assistant":
                pre="<bot>"
            else:
                print("do not support the role", item["role"])
            prompt +=  f"{pre}: {item['content']}\n"
        # prompt = "\n".join([
        #     f"<human>: {item['content']}" if item["role"] in ["user","system"] else f"<bot>: {item['content']}"
        #     for item in messages
        # ])

        prompt = prompt + "(only reply to this dialogue by one utterance, don't need to simulate the further dialogue)\n<bot>: "
        # print("prompt to llama============>: ", prompt)

        res = requests.post("https://api.together.xyz/inference", json={
            "model":  "togethercomputer/llama-2-70b-chat",
            "max_tokens": self.max_tokens,
            "prompt": prompt,
            "request_type": "language-model-inference",
            "temperature": self.temperature,
            "top_p": 0.7,
            "top_k": 50,
            "repetition_penalty": 1,
            "stop":[
                "[INST]"
            ],
            "safety_model": ""
        }, headers={
            "Authorization": "Bearer " + "dfc4d6a93871112a260d0812b6c26809c985652299b1bd93a4ff7c9f735de3b0"
        })
        response = res.json()["output"]["choices"][0]["text"]
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
        # print("======current history========: ", agent_name)
        # if agent_name.startswith("Player"):
        # # if agent_name == "Player 3":
        #     for msg in messages:
        #         if msg["role"] == "system":
        #             continue
        #         print("msg of", msg["role"])
        #         print(msg["content"].replace("\n",""))

        response = self._get_response(messages, *args, **kwargs)
        # print("response: ", response)

        # Remove the agent name if the response starts with it
        response = re.sub(rf"^\s*\[.*]:", "", response).strip()
        response = re.sub(rf"^\s*{re.escape(agent_name)}\s*:", "", response).strip()

        # Remove the tailing end of message token
        response = re.sub(rf"{END_OF_MESSAGE}$", "", response).strip()
        print("response: ", response)

        return response
