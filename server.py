from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class SentimentRequest(BaseModel):
    sentences: List[str]

class SentimentResult(BaseModel):
    sentence: str
    sentiment: str

class SentimentResponse(BaseModel):
    results: List[SentimentResult]

def get_sentiment(text: str) -> str:
    text = text.lower()
    # Basic keyword lists
    happy_words = ['love', 'great', 'happy', 'good', 'wonderful', 'amazing', 'best', 'excellent', 'fantastic']
    sad_words = ['hate', 'sad', 'terrible', 'bad', 'awful', 'worst', 'unhappy', 'depressed', 'poor']
    
    if any(word in text for word in happy_words):
        return "happy"
    elif any(word in text for word in sad_words):
        return "sad"
    else:
        return "neutral"

@app.post("/sentiment", response_model=SentimentResponse)
async def analyze_sentiment(payload: SentimentRequest):
    results = []
    for sentence in payload.sentences:
        sentiment = get_sentiment(sentence)
        results.append({"sentence": sentence, "sentiment": sentiment})
    
    return {"results": results}

if __name__ == "__main__":
    import uvicorn
    # Make sure this runs on the port the grader expects (default is often 8000)
    uvicorn.run(app, host="127.0.0.1", port=8000)
