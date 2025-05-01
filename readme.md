# WNTR GPT Simulation API

A REST API for running hydraulic simulations using WNTR and interpreting results using GPT-4. Built with FastAPI, deployable to Render.

## Endpoints

- `POST /simulate` – Upload `.inp` and run simulation
- `POST /analyze` – Run optional advanced analysis
- `POST /ask` – Get GPT-4 response on simulation summary

## Deployment (Render)

1. Push this repo to GitHub
2. Create a new Render Web Service
3. Set `OPENAI_API_KEY` in environment variables
4. Done 🚀

## Local Testing

```bash
uvicorn main:app --reload
