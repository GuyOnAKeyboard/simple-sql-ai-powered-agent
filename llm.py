from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI


def get_llm(provider: str):
    provider = provider.lower()

    if provider == "google":
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0,
        )

    elif provider == "ollama":
        return ChatOllama(
            model="qwen2.5:7b",
            temperature=0,
            streaming=True,
        )

    raise ValueError(
        f"Unsupported provider '{provider}'. Choose from: google, ollama."
    )


if __name__ == "__main__":
    llm = get_llm("ollama")
    response = llm.invoke("What is tool calling in LangChain?")
    print(response.content)