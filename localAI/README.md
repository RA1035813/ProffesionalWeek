 Inhoud van localAI/:


   1. knowledge_base.txt: Jouw eigen "dataset" met agronomische regels voor Tanzania. Hier kun je meer data aan toevoegen (zoals PDF-teksten of handboeken).
   2. rag_engine.py: De logica die de juiste regels uit de dataset haalt op basis van de sensordata.
   3. local_inference.py: De brug naar Ollama. Dit script vervangt de Gemini API en stuurt de sensordata samen met de gevonden RAG-context naar een lokaal model (zoals Mistral of Llama 3).


  Hoe dit werkt:
  In plaats van een algemene vraag aan Gemini te stellen ("Wat moet ik doen met deze pH?"), stuur je nu een specifieke instructie naar je lokale AI:
  > "Gebruik deze regel uit mijn database: 'pH < 5.0 -> Voeg as toe'. De sensor meet nu 4.8. Schrijf een SMS."


  Volgende stappen om dit te draaien:
   1. Installeer Ollama: Download het op je server/laptop (ollama.com (https://ollama.com)).
   2. Download een model: Draai ollama run mistral of ollama run llama3.
   3. Activeer in je server: Je kunt in analysis_server.py de functie generate_ai_advice simpelweg laten verwijzen naar local_inference.get_local_ai_advice.
