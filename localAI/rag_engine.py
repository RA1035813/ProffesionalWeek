import os

class SimpleRAG:
    """A light RAG implementation that finds relevant keywords in the KB."""
    def __init__(self, kb_path="localAI/knowledge_base.txt"):
        self.kb_content = ""
        if os.path.exists(kb_path):
            with open(kb_path, 'r') as f:
                self.kb_content = f.read()
        else:
            print(f"Warning: Knowledge base {kb_path} not found.")

    def get_relevant_context(self, sensor_data, weather_data):
        """
        Simple keyword-based context extraction.
        For a light local prototype, we select sections of the KB 
        that match the sensor status (e.g., pH < 5.0).
        """
        context = []
        
        # PH Logic
        ph = sensor_data.get('ph', 7.0)
        if ph < 5.5:
            context.append("PH is low (acidic). Use lime or ash.")
        elif ph > 8.0:
            context.append("PH is high (alkaline). Use compost.")

        # NPK Logic
        n = sensor_data.get('nitrogen_mg_kg', 150)
        if n < 100:
            context.append("Nitrogen is low. Recommend Urea or NPK.")

        # Weather Logic
        rain = weather_data.get('precipitation_sum', [0])[0]
        if rain > 15:
            context.append("Heavy rain expected (>15mm). Ensure drainage. Don't fertilize now.")
            
        # Return the most relevant 2-3 sentences from the full KB or custom logic
        return "\n".join(context)

# Testing the RAG engine
if __name__ == "__main__":
    rag = SimpleRAG()
    test_sensors = {'ph': 4.5, 'nitrogen_mg_kg': 50}
    test_weather = {'precipitation_sum': [20.5]}
    print("Relevant Context:")
    print(rag.get_relevant_context(test_sensors, test_weather))
