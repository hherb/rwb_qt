from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.models import ModelFactory
from camel.types import ModelPlatformType

ollama_model = ModelFactory.create(
    model_platform=ModelPlatformType.OLLAMA,
    model_type="phi4:latest",
    url="http://localhost:11434/v1", # Optional
    model_config_dict={"temperature": 0.4},
)

agent_sys_msg = "You are a helpful assistant."

agent = ChatAgent(agent_sys_msg, model=ollama_model, token_limit=4096)

user_msg = "Say hi to CAMEL"

assistant_response = agent.step(user_msg)
print(assistant_response.msg.content)
