# Neuralic AI – Realtime Voice Assistant

### Features
- GPT-4o Realtime voice
- Text chat
- Image generation
- Memory (Pinecone)
- AI actions
- WebSocket audio streaming

### Deploy on Render
1. Upload all files to GitHub
2. Create new Web Service on Render
3. Add environment variables:
- OPENAI_API_KEY
- PINECONE_API_KEY
- PINECONE_ENVIRONMENT
- PINECONE_INDEX
- APP_SECRET

### Start Command:
uvicorn main:app --host 0.0.0.0 --port 10000
