class LLMAdvisor:
    def __init__(self):
        pass

    def get_strategic_advice(self, stats, api_key=None):
        """
        Generates strategic advice based on hospital stats using local heuristic rules.
        Works entirely OFFLINE.
        """
        yield "### 🏥 Strategic AI Analysis\n\n"
        
        # 1. Analyze ICU
        if stats.get('occ_icu', 0) > 85:
            yield "- **CRITICAL**: ICU Bed saturation is at {:.1f}%. Action: Implementing 'Strategic Reservation' for arriving high-criticality cases. Non-acute transfers suggested.\n".format(stats['occ_icu'])
        elif stats.get('occ_icu', 0) > 60:
            yield "- **WARNING**: ICU capacity is tightening ({:.1f}%). Monitoring Emergency Department for potential escalations.\n".format(stats['occ_icu'])
        
        # 2. Analyze Staffing
        if stats.get('staff_ratio', 0) > 3.5:
            yield "- **STAFFING ALERT**: Nurse-to-patient ratio is {:.1f} (Threshold: 4.0). Suggest calling 'Float Pool' staff or activating additional shifts to prevent burnout and safety violations.\n".format(stats['staff_ratio'])
        
        # 3. Analyze Queues
        total_q = stats.get('queue_gen', 0) + stats.get('queue_icu', 0) + stats.get('queue_emer', 0)
        if total_q > 15:
            yield "- **BOTTLENECK**: Combined queue depth is {}. Suggesting 'Fast-Track' protocol for stable General Ward patients to expedite discharges.\n".format(total_q)
        
        # 4. Financials/Efficiency
        if stats.get('profit', 0) < 0:
            yield "- **FINANCIALS**: Operating in deficit (${:,.0f}). Optimize resource allocation to capture high-severity reimbursement codes vs overhead costs.\n".format(stats['profit'])
        
        if not any([stats.get('occ_icu', 0) > 85, stats.get('staff_ratio', 0) > 3.5, total_q > 15]):
            yield "- **SYSTEM STATUS**: All metrics within optimal thresholds. Maintaining current baseline resource distribution.\n"

    async def get_strategic_advice_async(self, stats, api_key=None):
        """
        Async version for FastAPI, yielding chunks to simulate 'thinking' or streaming.
        """
        import asyncio
        for chunk in self.get_strategic_advice(stats, api_key):
            yield chunk
            await asyncio.sleep(0.05) # Small sleep to show streaming in UI
