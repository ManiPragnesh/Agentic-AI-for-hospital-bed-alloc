from openai import OpenAI
import time

class LLMAdvisor:
    def __init__(self):
        pass

    def get_strategic_advice(self, stats, api_key):
        """
        Generates strategic advice based on hospital stats using OpenAI API.
        Yields chunks of text for streaming.
        """
        if not api_key:
            yield "⚠️ Please provide an OpenAI API Key in the sidebar to use the AI Advisor."
            return

        try:
            client = OpenAI(api_key=api_key)
            
            # Construct Prompt
            system_prompt = "You are an expert Hospital Operations Administrator. Analyze the provided hospital metrics and suggest 3 specific, actionable strategies to improve efficiency, reduce waiting times, or optimize financial performance."
            
            user_content = f"""
            Current Hospital Status:
            - Queues: General={stats['queue_gen']}, ICU={stats['queue_icu']}, Emergency={stats['queue_emer']}
            - Bed Occupancy: General={stats['occ_gen']}%, ICU={stats['occ_icu']}%
            - Financials: Revenue=${stats['revenue']}, Cost=${stats['cost']}, Profit=${stats['profit']}
            - Staff Strain Ratio: {stats['staff_ratio']} (Safe limit: 4.0)
            
            Identify the critical bottleneck and provide a concise strategic plan.
            """
            
            stream = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                stream=True,
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"❌ Error communicating with OpenAI: {str(e)}"

    async def get_strategic_advice_async(self, stats, api_key):
        """
        Async version for FastAPI.
        """
        from openai import AsyncOpenAI
        if not api_key:
            yield "⚠️ Please provide an OpenAI API Key."
            return

        try:
            client = AsyncOpenAI(api_key=api_key)
            
            system_prompt = "You are an expert Hospital Operations Administrator. Analyze the provided hospital metrics and suggest 3 specific, actionable strategies to improve efficiency, reduce waiting times, or optimize financial performance."
            
            user_content = f"""
            Current Hospital Status:
            - Queues: General={stats['queue_gen']}, ICU={stats['queue_icu']}, Emergency={stats['queue_emer']}
            - Bed Occupancy: General={stats.get('occ_gen', 0):.1f}%, ICU={stats.get('occ_icu', 0):.1f}%
            - Financials: Revenue=${stats['revenue']}, Cost=${stats['cost']}, Profit=${stats['profit']}
            - Staff Strain Ratio: {stats['staff_ratio']:.2f}
            
            Identify the critical bottleneck and provide a concise strategic plan.
            """
            
            stream = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"❌ Error: {str(e)}"
