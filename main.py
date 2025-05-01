from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import tempfile
import pandas as pd
import wntr
import openai
import os

app = FastAPI(
    title="WNTR GPT Simulation API",
    description="REST API for hydraulic simulation and GPT-assisted analysis of water distribution networks using WNTR and EPANET.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.get("/")
def read_root():
    return {"message": "WNTR GPT API is live. Use /simulate, /analyze, or /ask."}

@app.post("/simulate")
async def run_simulation(
    inp_file: UploadFile = File(...),
    simulation_type: str = Form("EPANET"),
    duration: int = Form(24),
    hydraulic_timestep: int = Form(60),
    demand_model: str = Form("PDD"),
    report_status: str = Form("YES")
):
    if not inp_file.filename.lower().endswith(".inp"):
        return JSONResponse(status_code=400, content={"error": "Only .inp files are supported."})

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".inp") as temp:
            temp.write(await inp_file.read())
            inp_path = temp.name

        wn = wntr.network.WaterNetworkModel(inp_path)
        wn.options.time.duration = duration * 3600
        wn.options.time.hydraulic_timestep = hydraulic_timestep * 60
        wn.options.hydraulic.demand_model = demand_model
        wn.options.report.status = report_status

        if simulation_type == "EPANET":
            sim = wntr.sim.EpanetSimulator(wn)
        else:
            sim = wntr.sim.WNTRSimulator(wn)

        results = sim.run_sim()
        pressure = results.node["pressure"]
        demand = results.node["demand"]

        return {
            "pressure": pressure.to_dict(),
            "demand": demand.to_dict()
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

class AnalysisRequest(BaseModel):
    analysis_type: str
    simulation_results: dict

@app.post("/analyze")
def run_advanced_analysis(request: AnalysisRequest):
    try:
        pressure_df = pd.DataFrame(request.simulation_results.get("pressure", {}))
        wn = wntr.network.WaterNetworkModel()  # Placeholder only

        if request.analysis_type == "Resilience":
            result = wntr.metrics.resilience.reliability(pressure_df)
            return {"result": round(result, 4)}

        elif request.analysis_type == "Economic Loss":
            population = wntr.metrics.population.estimate_population(wn)
            results = wntr.sim.WNTRSimulator(wn).run_sim()
            loss = wntr.metrics.economic_loss.economic_loss(results, population)
            return {"result": round(loss.sum().sum(), 2)}

        return {"result": "Analysis type not implemented or requires network state."}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

class GPTRequest(BaseModel):
    user_question: str
    pressure_summary: str
    demand_summary: str

@app.post("/ask")
def ask_gpt_assistant(request: GPTRequest):
    try:
        prompt = f"""
You are a hydraulic engineering assistant. The user has run a water network simulation.
Here is a summary of node pressures:
{request.pressure_summary}

Here is a summary of node demands:
{request.demand_summary}

Now answer the user's question: "{request.user_question}"
"""
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a civil engineering assistant who specializes in hydraulic analysis using EPANET and WNTR."},
                {"role": "user", "content": prompt}
            ]
        )
        answer = response["choices"][0]["message"]["content"]
        return {"answer": answer}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})




       
   



   
       
