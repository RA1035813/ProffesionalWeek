#!/bin/bash

# SoilSMS Automation Script for Linux, WSL, and macOS
# --------------------------------------------------

# Kleuren voor output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}==============================================${NC}"
echo -e "${GREEN}      SoilSMS Prototype - Setup & Run         ${NC}"
echo -e "${BLUE}==============================================${NC}"

# 1. Controleer Python
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}[!] Python3 is niet gevonden. Installeer Python3 om door te gaan.${NC}"
    exit 1
fi

# 2. Installeer dependencies
echo -e "\n${BLUE}[1/4] Bezig met installeren van Python dependencies...${NC}"
pip3 install -r requirements.txt --quiet
echo -e "${GREEN}[V] Dependencies geïnstalleerd.${NC}"

# 3. Controleer Ollama
echo -e "\n${BLUE}[2/4] Controleren van Ollama (Lokale AI)...${NC}"
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}[!] Ollama is niet geïnstalleerd.${NC}"
    read -p "Wilt u Ollama nu installeren? (j/n): " install_ollama
    if [[ $install_ollama == "j" ]]; then
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            curl -fsSL https://ollama.com/install.sh | sh
        else
            echo -e "${YELLOW}Ga naar https://ollama.com om de macOS versie te downloaden.${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}Ollama overslaan. U kunt alleen Gemini (Cloud) gebruiken.${NC}"
    fi
else
    echo -e "${GREEN}[V] Ollama is aanwezig.${NC}"
    # Zorg dat mistral gedownload is
    echo -e "${BLUE}Zorgen dat Mistral model aanwezig is...${NC}"
    ollama pull mistral --quiet
fi

# 4. Keuze: Lokaal of Cloud
echo -e "\n${BLUE}[3/4] Configuratie:${NC}"
echo "Welke AI mode wilt u gebruiken?"
echo "1) Lokaal (Mistral via Ollama) - Geen internet nodig voor AI"
echo "2) Cloud (Gemini API) - Vereist GEMINI_API_KEY in .env"
read -p "Maak uw keuze (1 of 2): " ai_choice

if [ "$ai_choice" == "1" ]; then
    sed -i 's/USE_LOCAL_AI = False/USE_LOCAL_AI = True/g' analysis_server.py 2>/dev/null || sed -i '' 's/USE_LOCAL_AI = False/USE_LOCAL_AI = True/g' analysis_server.py
    echo -e "${GREEN}[V] Geconfigureerd voor LOKALE AI.${NC}"
else
    sed -i 's/USE_LOCAL_AI = True/USE_LOCAL_AI = False/g' analysis_server.py 2>/dev/null || sed -i '' 's/USE_LOCAL_AI = True/USE_LOCAL_AI = False/g' analysis_server.py
    echo -e "${GREEN}[V] Geconfigureerd voor GEMINI CLOUD AI.${NC}"
    if [ ! -f .env ] || ! grep -q "GEMINI_API_KEY=AI" .env; then
        echo -e "${YELLOW}[!] Vergeet niet uw API key in de .env file te zetten!${NC}"
    fi
fi

# 5. Starten
echo -e "\n${BLUE}[4/4] SoilSMS Prototype opstarten...${NC}"
echo -e "${YELLOW}Druk op Ctrl+C om beide processen te stoppen.${NC}"

# Start server op de achtergrond
python3 analysis_server.py &
SERVER_PID=$!

# Wacht even tot server up is
sleep 3

# Start node
python3 sensor_node.py &
NODE_PID=$!

# Zorg dat bij afsluiten beide processen stoppen
trap "kill $SERVER_PID $NODE_PID; echo -e '\n${BLUE}SoilSMS gestopt.${NC}'; exit" INT

wait
