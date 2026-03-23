import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from prompts.templates import SUPERVISOR_PROMPT
load_dotenv()
llm = ChatOpenAI(model='gpt-4o', temperature=0.1, openai_api_key=os.getenv('OPENAI_API_KEY'))

class SupervisorAgent:

    def __init__(self):
        self.chain = SUPERVISOR_PROMPT | llm | JsonOutputParser()

    def route(self, user_query: str, messages: list) -> dict:
        try:
            result = self.chain.invoke({'user_query': user_query, 'messages': messages})
            if not isinstance(result.get('route'), list):
                result['route'] = ['analyst']
            if not result.get('symbols'):
                result['symbols'] = []
            if not result.get('reasoning'):
                result['reasoning'] = 'Defaulting to analyst agent.'
            return result
        except (json.JSONDecodeError, Exception) as e:
            return {'route': ['analyst'], 'reasoning': f'Routing fallback due to parsing error: {str(e)}', 'symbols': []}
