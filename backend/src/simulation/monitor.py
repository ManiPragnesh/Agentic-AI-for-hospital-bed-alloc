import json
import os
import time
import pandas as pd
import numpy as np

class Monitor:
    def __init__(self, hospital):
        self.hospital = hospital
        self.logs_buffer = []
        self.recent_events = [] # For RL Reward tracking
        self.log_file_path = None
        self.wall_start_time = time.time()
        self.sim_start_time = 0 # Will be set on first tick or init
        
        # Financials
        self.financial_stats = {
            'revenue_by_dept': {'General': 0, 'ICU': 0, 'Emergency': 0},
            'cost_by_dept': {'General': 0, 'ICU': 0, 'Emergency': 0},
            'staff_cost': 0,
            'overtime_cost': 0,
            'override_penalty': 0
        }
        
        # Global Counters
        self.total_patients = 0
        self.total_admissions = 0
        self.total_discharges = 0
        self.total_wait_time = 0.0
        self.total_deaths = 0
        self.total_unsafe_violations = 0
        self.peak_icu_queue = 0
        self.max_staff_strain = 0.0
        
        # Bed occupancy history for averaging
        self.occupancy_history = {'General': [], 'ICU': [], 'Emergency': []}
        
        # Initialize Log File
        self._init_log_file()

    def _init_log_file(self):
        timestamp = int(time.time())
        filename = f"simulation_run_{timestamp}.json"
        os.makedirs("backend/logs", exist_ok=True)
        self.log_file_path = os.path.join("backend/logs", filename)
        
        # Initialize file with empty array for valid JSON
        with open(self.log_file_path, 'w') as f:
            f.write('[') # Start of JSON Array

    def _flush_buffer(self):
        if not self.logs_buffer: return
        
        with open(self.log_file_path, 'a') as f:
            for entry in self.logs_buffer:
                f.write(json.dumps(entry) + ",\n")
        self.logs_buffer = []

    def calculate_hsi(self, staff_strain, icu_queue, financials):
        """
        Hospital Stability Index (0-100)
        Starts at 100.
        - Deduct for Staff Strain > 1.0 (Heavy penalty)
        - Deduct for ICU Queue > 5
        - Deduct for Financial Loss
        """
        score = 100
        
        # 1. Staff Strain Penalty
        if staff_strain > 1.0:
            penalty = (staff_strain - 1.0) * 50 # e.g. 1.2 -> -10 pts
            score -= penalty
        
        # 2. ICU Crisis Penalty
        if icu_queue > 5:
            score -= (icu_queue - 5) * 5 # -5 pts per extra patient
            
        # 3. Financial Health
        profit = financials['profit']
        if profit < 0:
            score -= 5 # Minor penalty for debt
            
        return max(0, min(100, score))

    def tick(self, sim_time):
        """
        Called every simulation step to log state.
        """
        if self.sim_start_time == 0:
            self.sim_start_time = sim_time

        # Gather Metrics
        depts = self.hospital.departments
        
        dept_metrics = {}
        max_strain = 0
        total_staff = self.hospital.state.get('total_staff', 0)
        
        for name, dept in depts.items():
            # Calculate Strain: (Patients / Staff) / Safe_Threshold
            # We assume uniform distribution of staff for now or use Dept specific tracking if available.
            # Simplified: Global Strain applied to all for now or check if Dept has staff count.
            # For V2, we have Dept.staff_count logic in Shift Scheduler?
            # Let's assume we can get it or fallback.
            d_staff = dept.staff_count if hasattr(dept, 'staff_count') else (total_staff // 3)
            d_safe_ratio = 4.0 if name != 'ICU' else 2.0 # stricter for ICU
            
            d_strain = 0
            if d_staff > 0:
                 d_current_ratio = len(dept.patients) / d_staff
                 d_strain = d_current_ratio / d_safe_ratio
            
            if d_strain > max_strain: max_strain = d_strain
            
            if d_strain > 1.0:
                self.total_unsafe_violations += 1
                
            # Track Occupancy
            self.occupancy_history[name].append(dept.beds.count / max(1, dept.beds.capacity))
            
            dept_metrics[name] = {
                'patients': len(dept.patients),
                'queue': len(dept.queue),
                'staff': d_staff,
                'strain': round(d_strain, 2)
            }
            
            if name == 'ICU' and len(dept.queue) > self.peak_icu_queue:
                self.peak_icu_queue = len(dept.queue)

        if max_strain > self.max_staff_strain:
            self.max_staff_strain = max_strain

        # Financials
        rev_total = sum(self.financial_stats['revenue_by_dept'].values())
        cost_total = sum(self.financial_stats['cost_by_dept'].values()) + \
                     self.financial_stats['staff_cost'] + \
                     self.financial_stats['overtime_cost'] + \
                     self.financial_stats['override_penalty']
        profit = rev_total - cost_total
        
        # HSI
        icu_q = dept_metrics.get('ICU', {}).get('queue', 0)
        hsi = self.calculate_hsi(max_strain, icu_q, {'profit': profit})

        log_entry = {
             'time': round(sim_time, 2),
             'type': 'STATE_TICK',
             'departments': dept_metrics,
             'global': {
                 'hsi': round(hsi, 1),
                 'profit': int(profit),
                 'total_violations': self.total_unsafe_violations
             }
        }
        
        self.logs_buffer.append(log_entry)
        
        # Flush every 10 ticks to avoid disk thrashing
        if len(self.logs_buffer) >= 10:
            self._flush_buffer()

    def log_event(self, time, event_type, message, details=None):
        if event_type == 'ARRIVAL':
            self.total_patients += 1
        elif event_type == 'ADMIT':
             self.total_admissions += 1
             if details and 'wait_time' in details:
                 self.total_wait_time += details['wait_time']
        elif event_type == 'DISCHARGE':
            self.total_discharges += 1
            # Calculate wait time if possible
            # Wait time = Admission time - Arrival time
            # Wait time calculation might be easier at the time of admission.
            # But let's look at the patient object if passed in details.
            pass
        elif 'DEATH' in event_type or 'CRITICAL_FAIL' in event_type:
            self.total_deaths += 1

        entry = {
            'time': round(time, 2),
            'type': 'EVENT',
            'Event': event_type, # Uppercase 'Event' to match reward logic in gym_env
            'message': message,
            'details': details or {}
        }
        self.logs_buffer.append(entry)
        
        # Track for RL
        self.recent_events.append(entry)
        if len(self.recent_events) > 100:
            self.recent_events.pop(0)
            
        self._flush_buffer() # Events are critical, save immediately

    def get_recent_events(self, count=10):
        events = self.recent_events[-count:]
        # Clear them so we don't double count rewards in next RL step? 
        # Actually, RL step() usually happens on every arrival.
        # It's better to clear them once read.
        self.recent_events = self.recent_events[:-count]
        return events

    def record_transaction(self, dept_name, revenue=0, cost=0, type='op'):
        if dept_name in self.financial_stats['revenue_by_dept']:
            self.financial_stats['revenue_by_dept'][dept_name] += revenue
            self.financial_stats['cost_by_dept'][dept_name] += cost
        elif type == 'staff':
            self.financial_stats['staff_cost'] += cost
        elif type == 'penalty':
             self.financial_stats['override_penalty'] += cost

    def get_accumulated_financials(self):
        # Legacy support for Dashboard
        rev = sum(self.financial_stats['revenue_by_dept'].values())
        cost = sum(self.financial_stats['cost_by_dept'].values()) + self.financial_stats['staff_cost']
        return {'revenue': int(rev), 'cost': int(cost), 'profit': int(rev - cost)}
        
    def get_logs_df(self):
        # Legacy support: read JSON logic? Or just keep in-memory for simpler API?
        # For huge logs, we shouldn't read from file. 
        # We'll just return simplified logs from buffer or a separate list we keep for UI
        # UI only needs last 50 events.
        # Let's keep a small deque for UI.
        return pd.DataFrame([x for x in self.logs_buffer if x.get('type') == 'EVENT']) 

    def _format_duration(self, hours):
        days = int(hours // 24)
        rem_hours = int(hours % 24)
        minutes = int((hours * 60) % 60)
        
        if days > 0:
            return f"{days}d {rem_hours}h {minutes}m"
        else:
            return f"{rem_hours}h {minutes}m"

    def close(self, current_sim_time=None):
        """
        Finalize log file.
        """
        duration = 0
        if current_sim_time is not None:
             duration = current_sim_time - self.sim_start_time
             
        # Final Summary
        summary = {
            'duration_hours': round(duration, 2),
            'duration_text': self._format_duration(duration),
            'peak_icu_queue': self.peak_icu_queue,
            'max_staff_strain': self.max_staff_strain,
            'total_unsafe_violations': self.total_unsafe_violations,
            'final_financials': self.financial_stats
        }
        
        entry = {
            'type': 'FINAL_SUMMARY',
            'summary': summary
        }
        # Adding prefix comma to avoid invalid JSON array
        self.logs_buffer.append(entry)
        
        # Flush the entry manually so we can prepend the comma correctly if needed,
        # but the simplest fix for an array is to just let _flush_buffer do its thing
        # since _flush_buffer always appends `,\n`
        self._flush_buffer()
        
        # Close Request
        # Remove trailing comma if exists and add ']'
        try:
            with open(self.log_file_path, 'r+') as f:
                content = f.read()
                content = content.rstrip()
                if content.endswith(','):
                    content = content[:-1]
                f.seek(0)
                f.write(content + ']')
                f.truncate()
        except Exception as e:
            print(f"Error finalizing JSON log: {e}")
             
        print(f"📁 Log saved to: {os.path.abspath(self.log_file_path)}")
        return self.log_file_path
