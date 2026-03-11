from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from starlette.staticfiles import StaticFiles
import simpy
import os
import sys
import asyncio
from pydantic import BaseModel
import pandas as pd

# Add project root to path (Hack to make dynamic loading work without package install)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from backend.simulation.env import HospitalSim
from backend.simulation.patient import patient_generator
from backend.agents.llm_advisor import LLMAdvisor
from backend.simulation.monitor import Monitor

api_app = FastAPI(title="Hospital Agentic AI API")

# CORS (Allow frontend access)
api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from datetime import datetime
from backend.simulation.patient import Patient

# Add PPO Import
from stable_baselines3 import PPO
import numpy as np

# Global Model
rl_model = None
model_path = os.path.join(os.path.dirname(__file__), "../rl/models/ppo_hospital_v1.zip")
if os.path.exists(model_path):
    try:
        rl_model = PPO.load(model_path)
        print("[INFO] RL Model Loaded")
    except Exception as e:
        print(f"[WARN] Failed to load RL Model: {e}")
else:
    print("[WARN] RL Model not found at", model_path)

# Global State Container
class SimulationState:
    def __init__(self):
        self.env = None
        self.hospital = None
        self.use_rl = False
        self.reset()
        
    def reset(self, config=None):
        # Auto-Save previous run if exists
        if self.hospital and self.hospital.monitor:
             # Capture end time
             end_time = self.env.now if self.env else 0
             path = self.hospital.monitor.close(current_sim_time=end_time)
             print(f"Stats saved to {path}")

        self.env = simpy.Environment()
        
        # Defaults
        c = config or {}
        beds = c.get('beds', 50)
        icu = c.get('icu_beds', 10)
        staff = c.get('staff', 20)
        rate = c.get('arrival_rate', 0.5)
        self.use_rl = c.get('use_rl', False)
        
        # Default config matching app.py sliders
        self.hospital = HospitalSim(self.env, beds=beds, icu_beds=icu, staff=staff)
        
        # Configure Agent Mode
        if self.use_rl and rl_model:
             self.hospital.admission_agent.mode = 'RL'
             print("[INFO] Hospital Agent: RL MODE ACTIVATED")
        else:
             self.hospital.admission_agent.mode = 'RULE_BASED'
             
        # Start Generator
        self.env.process(patient_generator(self.env, self.hospital, arrival_rate=rate))
        print(f"Simulation Reset with config: {c}")

    def get_gym_obs(self):
        # Construct V4 State Vector (Must match GymEnv)
        depts = self.hospital.departments
        
        gen_q = len(depts['General'].queue)
        icu_q = len(depts['ICU'].queue)
        emer_q = len(depts['Emergency'].queue)
        
        gen_occ = depts['General'].beds.count / max(1, depts['General'].beds.capacity)
        icu_occ = depts['ICU'].beds.count / max(1, depts['ICU'].beds.capacity)
        
        staff_ratio = self.hospital.state.get('current_patients', 0) / max(1, self.hospital.state.get('total_staff', 1))
        
        patient = getattr(self.hospital, 'current_patient', None)
        sev = patient.severity if patient else 0
        
        return np.array([
            gen_q, icu_q, emer_q,
            gen_occ, icu_occ,
            staff_ratio,
            sev,
            0 # Padding
        ], dtype=np.float32)

sim_state = SimulationState()

@api_app.get("/")
def read_root():
    return {"status": "Running", "service": "Hospital Agentic AI Backend"}

from backend.simulation.scenarios import ScenarioManager

# ... (imports)

class SimConfig(BaseModel):
    beds: int = 50
    icu_beds: int = 10
    staff: int = 20
    arrival_rate: float = 0.5
    use_rl: bool = False
    scenario: str = "NORMAL"

@api_app.post("/simulation/reset")
def reset_simulation(config: SimConfig = None):
    try:
        if not config:
            config = SimConfig()
            
        # Apply Scenario Logic
        base_config = config.dict()
        scenario_config = ScenarioManager.get_config(config.scenario, base_config)
        
        sim_state.reset(scenario_config)
        return {"message": "Simulation Reset", "time": 0, "config": scenario_config}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

class PatientRequest(BaseModel):
    severity: int
    care_type: str # 'General', 'ICU', 'Emergency'

@api_app.post("/simulation/admit")
def admit_manual_patient(req: PatientRequest):
    """
    Manually injects a patient into the simulation.
    """
    if not sim_state.env:
        raise HTTPException(status_code=400, detail="Simulation not started")
        
    # Create Patient Logic (must happen in SimPy context effectively)
    # We can just process it because SimPy is paused between "runs"
    
    # Generate ID
    pid = f"MANUAL-{int(datetime.now().timestamp())}"
    
    monitor = sim_state.hospital.monitor if sim_state.hospital else None
    
    p = Patient(pid, sim_state.env, monitor=monitor, severity=req.severity, care_type=req.care_type)
    
    # Schedule handling
    sim_state.env.process(sim_state.hospital.handle_patient(p))
    
    return {"message": f"Patient {pid} scheduled for admission", "patient": req.dict()}

class StepRequest(BaseModel):
    hours: int = 1

@api_app.post("/simulation/step")
def step_simulation(req: StepRequest):
    """
    Advances simulation by X hours.
    """
    try:
        current_time = sim_state.env.now
        target_time = current_time + req.hours
        
        while sim_state.env.now < target_time:
             print(f"[DEBUG] Step Loop: Now={sim_state.env.now:.2f}, Target={target_time:.2f}")
             if sim_state.use_rl and rl_model:
                 remaining = target_time - sim_state.env.now
                 if remaining <= 0: break
                 
                 gym_event = sim_state.hospital.gym_needs_action
                 timeout_event = sim_state.env.timeout(remaining)
                 
                 res = sim_state.env.run(until=simpy.AnyOf(sim_state.env, [gym_event, timeout_event]))
                 
                 if gym_event in res.events:
                     # RL Decision
                     print("[DEBUG] RL Event Triggered")
                     obs = sim_state.get_gym_obs()
                     action, _ = rl_model.predict(obs)
                     
                     action_map = {0: 'ADMIT_General', 1: 'ADMIT_ICU', 2: 'ADMIT_Emergency', 3: 'TRANSFER'}
                     action_str = action_map.get(int(action), 'TRANSFER')
                     
                     sim_state.hospital.last_action_from_gym = action_str
                     sim_state.hospital.receive_action.succeed()
                     sim_state.hospital.receive_action = sim_state.env.event()
                     sim_state.hospital.gym_needs_action = sim_state.env.event()
                 else:
                     print("[DEBUG] Timeout Triggered (Step Complete)")
                     break
             else:
                 sim_state.env.run(until=target_time)
                 break
            
        return {
            "previous_time": current_time,
            "current_time": sim_state.env.now,
            "steps_advanced": req.hours
        }
    except Exception as e:
        # Traceback for easier debugging
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@api_app.get("/metrics")
def get_metrics():
    """
    Returns current expanded state of the simulation.
    """
    hosp = sim_state.hospital
    
    # Financials
    fin = hosp.monitor.get_accumulated_financials()
    
    # Department Breakdown
    depts = {}
    for name, d in hosp.departments.items():
        depts[name] = {
            "queue_length": len(d.queue),
            "occupancy": d.beds.count,
            "capacity": d.beds.capacity,
            "staff_active": d.staff_count,
            "patients": len(d.patients)
        }

    # Staff Ratio
    status = hosp.staff_agent.get_status(hosp.state['current_patients'], hosp.state['total_staff'])
    
    # Event Log (Last 10)
    # Monitor logs are now list of dicts from buffer
    logs = sim_state.hospital.monitor.get_logs_df().tail(10).to_dict(orient='records') if not sim_state.hospital.monitor.get_logs_df().empty else []

    # Calculate latest HSI directly or retrieve from last tick?
    # Better to just calc it on the fly or grab last log.
    # Let's grab simple stats from monitor
    hsi_score = 100
    if sim_state.hospital.monitor.logs_buffer:
        last = sim_state.hospital.monitor.logs_buffer[-1]
        if last.get('type') == 'STATE_TICK':
             hsi_score = last['global']['hsi']

    return {
        "time": sim_state.env.now,
        "financials": fin,
        "departments": depts,
        "staff_status": status,
        "recent_logs": logs,
        "global": {
            "hsi": hsi_score,
            "violations": sim_state.hospital.monitor.total_unsafe_violations
        }
    }

class AdvisorRequest(BaseModel):
    api_key: str

@api_app.post("/analyze/advisor")
async def get_advice(req: AdvisorRequest):
    """
    Streams advice from OpenAI based on current metrics.
    """
    metrics = get_metrics()
    
    # Flatten metrics for LLM
    stats = {
        'queue_gen': metrics['departments']['General']['queue_length'],
        'queue_icu': metrics['departments']['ICU']['queue_length'],
        'queue_emer': metrics['departments']['Emergency']['queue_length'],
        'occ_gen': (metrics['departments']['General']['occupancy'] / max(1, metrics['departments']['General']['capacity'])) * 100,
        'occ_icu': (metrics['departments']['ICU']['occupancy'] / max(1, metrics['departments']['ICU']['capacity'])) * 100,
        'revenue': metrics['financials']['revenue'],
        'cost': metrics['financials']['cost'],
        'profit': metrics['financials']['profit'],
        'staff_ratio': metrics['staff_status']['ratio'],
        # New Metrics
        'hsi': metrics.get('global', {}).get('hsi', 100), # we need to expose HSI in get_metrics first!
        'usafe_violations': sim_state.hospital.monitor.total_unsafe_violations if sim_state.hospital else 0
    }
    
    # Log Payload
    if sim_state.hospital:
        sim_state.hospital.monitor.log_event(sim_state.env.now, 'LLM_REQUEST', "Sending context to Advisor", stats)
    
    advisor = LLMAdvisor()
    
    async def event_generator():
        full_response = ""
        async for chunk in advisor.get_strategic_advice_async(stats, req.api_key):
             full_response += chunk
             yield chunk
             # Small delay to simulate typing if too fast, but usually network is bottleneck
             # await asyncio.sleep(0.05) 

        # Log Response
        if sim_state.hospital:
             sim_state.hospital.monitor.log_event(sim_state.env.now, 'LLM_RESPONSE', "Advisor Reply", {'text': full_response[:500] + "..."}) # Truncate

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Unified parent application serving API and Frontend
app = FastAPI(title="Unified Hospital Agentic AI")

# Mount API under /api
app.mount("/api", api_app)

# Serve static frontend (Next.js export) when available; otherwise optionally proxy to Next dev
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/out"))
DEV_PROXY = os.environ.get("DEV_PROXY", "0") == "1"

if os.path.isdir(STATIC_DIR) and not DEV_PROXY:
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend")
else:
    # Optional dev proxy to Next.js (single-port dev)
    try:
        import httpx
    except Exception:
        httpx = None

    @app.api_route("/{path:path}", methods=["GET"])
    async def proxy_frontend(request: Request, path: str = ""):
        if not DEV_PROXY or httpx is None:
            return Response(
                content="Frontend build not found. Run `npm run build && npx next export` in frontend/.",
                media_type="text/plain",
                status_code=200,
            )
        target = f"http://localhost:3000/{path}"
        async with httpx.AsyncClient(follow_redirects=True) as client:
            upstream = await client.get(target, headers=dict(request.headers))
            return Response(content=upstream.content, status_code=upstream.status_code, headers=dict(upstream.headers))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
