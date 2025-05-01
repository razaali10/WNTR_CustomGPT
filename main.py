@app.post("/simulate")
async def run_simulation(
    inp_file: UploadFile = File(...),
    simulation_type: str = Form("EPANET"),
    duration: int = Form(24),
    hydraulic_timestep: int = Form(60),
    demand_model: str = Form("PDD"),
    report_status: str = Form("YES")
):
    # ✅ Validate file extension
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
