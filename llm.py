from langchain_ollama import ChatOllama


llm = ChatOllama(
    model="qwen2.5:7b",
    temperature=0,
    streaming=True
)

if __name__=="__main__":
    response = llm.invoke("What is tool calling in langchain?")
    print("\nResponse Content: ", response.content)