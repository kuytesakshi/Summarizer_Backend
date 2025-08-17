from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from langgraph.graph import StateGraph , START , END
from typing import TypedDict

load_dotenv()

class Output(BaseModel):
    summary: list[str] = Field(description="A good summary based on the given instructions.")

# Define parser
parser = PydanticOutputParser(pydantic_object=Output)

# Define LLM
llm = ChatGroq(
    model="deepseek-r1-distill-llama-70b",
    temperature=0,
)

# Define the chat prompt
template = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a very good notes summarizer. Follow these instructions:\n{instructions}"),
        ("human", "{notes}\n Also give the answer only in the format given below: \n{format_instructions}"),
    ]
).partial(format_instructions=parser.get_format_instructions())


class SummarySate(TypedDict):
    instructions: str
    notes: str
    summary: list[str]

def generate_summary(state: SummarySate):
    notes = state["notes"]
    instructions = state["instructions"]
    chain = template | llm | parser
    ai_msg = chain.invoke({
        "instructions": f"{instructions}",
        "notes": f"""{notes}"""
            })
    return {"summary" : ai_msg.summary}


graph = StateGraph(SummarySate)
graph.add_node("generate_summary" , generate_summary)

graph.add_edge(START , "generate_summary")
graph.add_edge("generate_summary" , END)

workflow = graph.compile()

# answer = workflow.invoke({"instructions" : "Give the concise summary for me.",
#                  "notes" : """
# Artificial Intelligence (AI) is a revolutionary branch of computer science that focuses on building intelligent systems capable of performing tasks that usually require human intelligence. These tasks include reasoning, problem-solving, decision-making, language understanding, and even creativity. AI systems rely on large volumes of data, advanced mathematical models, and powerful computing resources to learn patterns and continuously improve their performance. Machine learning, a subset of AI, enables computers to automatically improve their predictions and recommendations through experience, while deep learning mimics the structure of the human brain with neural networks to achieve remarkable results in image recognition, speech processing, and natural language understanding. Today, AI applications are embedded in almost every aspect of daily life — from voice assistants and personalized recommendations to fraud detection, medical diagnostics, autonomous vehicles, and robotics. Businesses leverage AI to optimize operations, predict market trends, and deliver personalized customer experiences, while researchers use it to solve complex problems in science, climate, and medicine. However, alongside its opportunities, AI raises important ethical and societal concerns such as data privacy, bias in decision-making, and the potential impact on jobs. As AI continues to evolve, it holds the potential to shape a future where humans and machines collaborate more closely than ever before."""})

# print(answer["summary"])

