import streamlit as st
import pandas as pd
import simpy
import time
import plotly.express as px
import numpy as np
import os
import sys

# Check imports - workaround for module paths if running from root
sys.path.append(os.getcwd())

from backend.src.simulation.env import HospitalSim
from backend.src.simulation.patient import patient_generator
from backend.src.agents.llm_advisor import LLMAdvisor # New Import
from stable_baselines3 import PPO

# Streamlit Config
st.set_page_config(page_title="Hospital Agentic AI", layout="wide")

st.title("🏥 Hospital Agentic AI - Real-Time Dashboard")

# Sidebar - Configuration
st.sidebar.header("Simulation Settings")
arrival_rate = st.sidebar.slider("Patient Arrival Rate (Patients/Hour)", 0.1, 2.0, 0.5)
# ...
total_beds = st.sidebar.slider("General Beds", 10, 100, 50)
icu_beds = st.sidebar.slider("ICU Beds", 2, 20, 10)
total_staff = st.sidebar.slider("Total Staff (Nurses/Doctors)", 5, 50, 20) # New Config
sim_speed = st.sidebar.select_slider("Simulation Speed", options=["Slow", "Normal", "Fast"], value="Normal")

# OpenAI Integration
st.sidebar.markdown("---")
openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password", help="Required for AI Advisor")

agent_mode = st.sidebar.radio("Admission Agent Mode", ["Rule-Based", "RL Agent (PPO)"])

st.sidebar.markdown("---")
st.sidebar.subheader("⚠ Scenario Triggers")
if st.sidebar.button("💥 Mass Casualty (4h)"):
    if 'hospital' in st.session_state:
        st.session_state.hospital.trigger_scenario('mass_casualty')
        st.toast("Mass Casualty Scenario Triggered!", icon="🚑")

if st.sidebar.button("🚌 Bus Accident (1h)"):
    if 'hospital' in st.session_state:
        st.session_state.hospital.trigger_scenario('bus_accident')
        st.toast("Bus Accident Scenario Triggered!", icon="🚌")

# State Management for Persistent Simulation
if 'env' not in st.session_state:
    st.session_state.env = simpy.Environment()
    # Pass total_staff
    st.session_state.hospital = HospitalSim(st.session_state.env, beds=total_beds, icu_beds=icu_beds, staff=total_staff)
    
    # Configure Agent Mode
    if agent_mode == "RL Agent (PPO)":
        st.session_state.hospital.admission_agent.mode = 'RL'
        # Load Model
        model_path = os.path.join(os.path.dirname(__file__), "rl/models/ppo_hospital_v1.zip")
        if os.path.exists(model_path):
            st.session_state.model = PPO.load(model_path)
            st.toast("RL Model Loaded Successfully!", icon="🤖")
        else:
            st.session_state.model = None
            st.error("Model not found! Using random fallback.")
    else:
        st.session_state.hospital.admission_agent.mode = 'RULE'
        st.session_state.model = None
        
    # Start Generator
    st.session_state.env.process(patient_generator(st.session_state.env, st.session_state.hospital, arrival_rate))
    
    # Data Buffers
    st.session_state.queue_history = []
    st.session_state.time_history = []
    st.session_state.bed_history = []
    st.session_state.staff_strain_history = [] # New Buffer

# Main Layout
tab1, tab2, tab3 = st.tabs(["📊 Overview", "🏥 Departments", "🔮 Analytics"])

with tab1:
    col1, col2, col3, col4 = st.columns(4) # Added col4
    with col1:
        queue_len_display = st.empty()
    with col2:
        occ_gen_display = st.empty()
    with col3:
        occ_icu_display = st.empty()
    with col4:
        staff_ratio_display = st.empty() 
    
    # Financials Row
    st.markdown("---")
    f_col1, f_col2, f_col3 = st.columns(3)
    rev_display = f_col1.empty()
    cost_display = f_col2.empty()
    profit_display = f_col3.empty()

    # Charts
    chart_placeholder = st.empty()
    strain_chart_placeholder = st.empty() 

with tab2:
    st.subheader("Department Status")
    dept_chart_placeholder = st.empty()
    
with tab3:
    st.subheader("Predictive Forecast (Next 12 Hours)")
    pred_chart_placeholder = st.empty()

# Simulation Control 
run_btn = st.sidebar.button("Run Simulation Step")
auto_run = st.sidebar.checkbox("Auto-Run (Continuous)")
# Move scenario buttons here (already done in previous step)

def run_step():
    # ... (existing step logic) ...
    # Run for 1 hour
    target_time = st.session_state.env.now + 1
    
    # Handling RL Pauses if needed
    try:
        # We need a loop because run(until=target) might stop early for RL event
        while st.session_state.env.now < target_time:
            
            # If RL mode and waiting for action
            if st.session_state.hospital.admission_agent.mode == 'RL' and st.session_state.hospital.gym_needs_action.triggered:
                
                # Construct Observation for Model (V2: 8 dims)
                hosp = st.session_state.hospital
                depts = hosp.departments
                
                # Department Queues
                gen_q = len(depts['General'].queue)
                icu_q = len(depts['ICU'].queue)
                emer_q = len(depts['Emergency'].queue)
                
                # Beds Free
                gen_free = depts['General'].beds.capacity - depts['General'].beds.count
                icu_free = depts['ICU'].beds.capacity - depts['ICU'].beds.count
                emer_free = depts['Emergency'].beds.capacity - depts['Emergency'].beds.count
                
                # Patient Info (Approximation as we don't have the object here easily without modifying env flow more)
                # But wait, we exposed `hosp.current_patient` in env.py!
                patient = getattr(hosp, 'current_patient', None)
                if patient:
                    sev = patient.severity
                    p_type = 0
                    if patient.care_type == 'Emergency': p_type = 1
                    elif patient.care_type == 'ICU': p_type = 2
                else:
                    sev = 3
                    p_type = 0
                
                obs = np.array([
                    gen_q, icu_q, emer_q,
                    gen_free, icu_free, emer_free,
                    sev, p_type
                ], dtype=np.float32)
                
                if st.session_state.model:
                    action_idx, _ = st.session_state.model.predict(obs)
                    action = 'ADMIT' if action_idx == 0 else 'REDIRECT'
                else:
                    import random
                    action = 'ADMIT' if random.random() > 0.1 else 'REDIRECT' 
                
                st.session_state.hospital.last_action_from_gym = action
                st.session_state.hospital.gym_needs_action = st.session_state.env.event() # Reset
                st.session_state.hospital.receive_action.succeed()
                st.session_state.hospital.receive_action = st.session_state.env.event()
            
            # Step simulation
            st.session_state.env.step()
            
    except simpy.Interrupt:
        pass
        
    # Collect Metrics
    hosp = st.session_state.hospital
    st.session_state.queue_history.append(len(hosp.waiting_queue))
    st.session_state.time_history.append(st.session_state.env.now)
    st.session_state.bed_history.append(total_beds - hosp.state['general_beds_free'])
    
    # Track Staff Strain
    pattern = hosp.staff_agent.get_status(hosp.state['current_patients'], hosp.state['total_staff'])
    st.session_state.staff_strain_history.append(pattern['ratio'])

if run_btn or auto_run:
    run_step()
    
    # Current Stats
    hosp = st.session_state.hospital
    q_len = len(hosp.waiting_queue)
    gen_occ = ((total_beds - hosp.state['general_beds_free']) / total_beds) * 100
    icu_occ = ((icu_beds - hosp.state['icu_beds_free']) / icu_beds) * 100
    
    status = hosp.staff_agent.get_status(hosp.state['current_patients'], hosp.state['total_staff'])
    ratio_val = status['ratio']
    
    queue_len_display.metric("Waiting Queue", q_len)
    occ_gen_display.metric("General Bed Occupancy", f"{gen_occ:.1f}%")
    occ_icu_display.metric("ICU Occupancy", f"{icu_occ:.1f}%")
    staff_ratio_display.metric("Avg Patients/Staff", f"{ratio_val:.1f}", delta_color="inverse" if not status['is_safe'] else "normal")
    
    # AI Advisor Insights (Generative AI)
    st.markdown("### 🧠 AI Strategic Advisor")
    
    if st.button("Generate Analysis (ChatGPT)"):
        advisor = LLMAdvisor()
        
        # Prepare Stats
        stats = {
            'queue_gen': len(hosp.departments['General'].queue),
            'queue_icu': len(hosp.departments['ICU'].queue), 
            'queue_emer': len(hosp.departments['Emergency'].queue),
            'occ_gen': gen_occ,
            'occ_icu': icu_occ,
            'stat_revenue': fin['revenue'], # Renamed to avoid confusion with local var
            'stat_cost': fin['cost'],
            'stat_profit': fin['profit'],
            'revenue': fin['revenue'],
            'cost': fin['cost'],
            'profit': fin['profit'],
            'staff_ratio': ratio_val
        }
        
        # Stream Response
        response_container = st.empty()
        collected_text = ""
        
        # Use spinner while waiting for first chunk
        with st.spinner('Consulting with AI Advisor...'):
            stream = advisor.get_strategic_advice(stats, openai_api_key)
            
            for chunk in stream:
                collected_text += chunk
                response_container.markdown(collected_text)

    # Fallback to simple alerts if no AI request
    if status['ratio'] > 4.0:
        st.warning(f"⚠️ **Critical Staff Strain**: Ratio {status['ratio']:.1f}")
    if q_len > 15:
        st.warning(f"⚠️ **High Queue**: {q_len} patients waiting.")
        
    # Financial Updates
    fin = hosp.monitor.get_accumulated_financials()
    rev_display.metric("Total Revenue", f"${fin['revenue']:,.0f}")
    cost_display.metric("Total Cost", f"${fin['cost']:,.0f}")
    profit_display.metric("Net Profit", f"${fin['profit']:,.0f}", delta_color="normal" if fin['profit'] > 0 else "inverse")
    
    # Update Charts (Tab 1)
    df = pd.DataFrame({
        "Time": st.session_state.time_history,
        "Queue Length": st.session_state.queue_history,
        "Bed Usage": st.session_state.bed_history,
        "Staff Ratio": st.session_state.staff_strain_history
    })
    
    if not df.empty:
        fig = px.line(df, x="Time", y=["Queue Length", "Bed Usage"], title="Hospital Operational Metrics")
        chart_placeholder.plotly_chart(fig, use_container_width=True)
        
        fig2 = px.area(df, x="Time", y="Staff Ratio", title="Staff Strain (Red > 4.0)", color_discrete_sequence=['red'])
        fig2.add_hline(y=4, line_dash="dash", annotation_text="Max Safe Ratio (1:4)")
        strain_chart_placeholder.plotly_chart(fig2, use_container_width=True)
        
    # Tab 2: Departments
    # Gather dept data
    dept_data = []
    for name, dept in hosp.departments.items():
        dept_data.append({
            "Department": name,
            "Patients": len(dept.patients),
            "Queue": len(dept.queue),
            "Staff": dept.staff_count
        })
    df_dept = pd.DataFrame(dept_data)
    fig_dept = px.bar(df_dept, x="Department", y=["Patients", "Queue", "Staff"], barmode='group', title="Department Breakdown")
    dept_chart_placeholder.plotly_chart(fig_dept, use_container_width=True)
    
    # Tab 3: Analytics (Foresting)
    if len(df) > 5:
        # Simple Logic: Project Queue based on Arrival Rate vs Discharge Rate
        last_q = df['Queue Length'].iloc[-1]
        
        # Get Monitor Rates
        avg_d_rate = hosp.monitor.get_recent_discharge_rate(st.session_state.env.now, window=5)
        # Access arrival rate from sidebar variable (global scope in streamlit script)
        # Note: 'arrival_rate' variable from sidebar
        
        # Net Change = Arrival - Discharge
        net_change = arrival_rate - avg_d_rate
        
        # Forecast 12 steps
        future_times = [st.session_state.env.now + i for i in range(1, 13)]
        future_q = [max(0, last_q + net_change * i) for i in range(1, 13)]
        
        df_pred = pd.DataFrame({"Time": future_times, "Predicted Queue": future_q})
        fig_pred = px.line(df_pred, x="Time", y="Predicted Queue", title=f"Queue Forecast (Net Rate: {net_change:.2f}/hr)")
        fig_pred.add_hline(y=0, line_dash="solid", line_color="green")
        pred_chart_placeholder.plotly_chart(fig_pred, use_container_width=True)
    
    if auto_run:
        time.sleep(0.1 if sim_speed == "Fast" else 0.5)
        st.rerun()

# Logs Section
st.subheader("Agent Decision Logs")
if 'hospital' in st.session_state:
    logs_df = st.session_state.hospital.monitor.get_logs_df()
    if not logs_df.empty:
        st.dataframe(logs_df.tail(10))
