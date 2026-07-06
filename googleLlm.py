import os
from langchain_google_genai import ChatGoogleGenerativeAI



if __name__=="__main__":
    response = google_llm.invoke("What is tool calling in langchain?")
    print("\nResponse Content: ", response.content)