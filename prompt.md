Je bent een Lead IoT & Backend Developer. Ik wil dat je me helpt met het bouwen van het software-prototype voor ons project "SoilSMS" (voor kleine boeren in Tanzania).

De strikte project-eisen (uit onze pitch):
1. De boer heeft GEEN smartphone of internet. De enige communicatie naar de boer is via een simpele SMS.
2. We gebruiken data om actiegericht landbouwadvies te geven (zoals gewasrotatie en waarschuwingen voor droogte/overstromingen).

De Architectuur (gebaseerd op ons draw.io schema):
Deel 1: 📍 Farm Node (Off-Grid / 2G Only)
- Een Raspberry Pi (of vergelijkbare microcontroller) die sensordata uitleest: Bodemvocht, pH-waarde, NPK-waarden en temperatuur.
- De node verstuurt deze gesimuleerde data via een 2G module (zoals SIM800L) of een simpele HTTP POST naar onze server.

Deel 2: ☁️ Cloud & Analysis (Backend)
- Een simpele server (bijv. in Python FastAPI of Flask) die de data van de Farm Node ontvangt.
- De server haalt actuele en voorspelde weerdata op via de (gratis) Open-Meteo API op basis van de locatie van de Farm Node.
- De server combineert de sensordata en de weerdata, en stuurt dit als een "Agronomy Prompt" naar een LLM (zoals de Gemini API).
- De LLM moet een kort, krachtig SMS-bericht van maximaal 160 tekens genereren met concreet advies voor de boer (bijv: "Bodem is te zuur. Plant komend seizoen bonen. Verwachte regen over 3 dagen.").

Deel 3: 📱 Send Advisory SMS
- De backend verstuurt de gegenereerde SMS via een SMS Gateway (zoals Twilio API) terug naar de telefoon van de boer.

Opdracht voor jou:
1. Geef me de aanbevolen folderstructuur voor dit project.
2. Schrijf het Python-script voor de 'Farm Node' (inclusief het simuleren van de sensordata, aangezien we het prototype lokaal testen).
3. Schrijf de Python backend code (FastAPI/Flask) die de data ontvangt, Open-Meteo aanroept, de Gemini API gebruikt voor de analyse, en de code bevat om de SMS te versturen.
4. Schrijf de specifieke systeem-prompt die we aan de LLM moeten meegeven zodat de output altijd een perfect leesbare SMS voor de boer is, zonder overbodige technische jargon.

Geef de code overzichtelijk weer in blokken voorzien van commentaar.
