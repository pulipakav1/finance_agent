import os
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from agents.agent_helpers import final_ai_text_from_messages, tool_calls_log_from_messages
from prompts.templates import NEWS_SYSTEM_PROMPT
from tools.stock_tools import get_stock_news, get_market_sentiment
load_dotenv()
llm = ChatOpenAI(model='gpt-4o', temperature=0.2, openai_api_key=os.getenv('OPENAI_API_KEY'))
NEWS_TOOLS = [get_stock_news, get_market_sentiment]

class NewsAgent:

    def __init__(self):
        self.graph = create_agent(model=llm, tools=NEWS_TOOLS, system_prompt=NEWS_SYSTEM_PROMPT)

    def analyze(self, query: str, chat_history: list=None) -> dict:
        messages = []
        if chat_history:
            messages.extend(chat_history)
        messages.append(HumanMessage(content=query))
        result = self.graph.invoke({'messages': messages}, config={'recursion_limit': 24})
        out_messages = result['messages']
        return {'output': final_ai_text_from_messages(out_messages), 'tool_calls_log': tool_calls_log_from_messages(out_messages)}
