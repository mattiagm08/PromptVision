import json
import os
from datetime import datetime

class UtilsManager:
    """
    Gestisce la persistenza dei dati (preset) e la registrazione 
    delle attività (log) durante la sessione.
    """
    def __init__(self):
        # FILE LOCALE PER LA PERSISTENZA DEI PRESET
        self.presetFile = "presets.json"

        # STORICO IN MEMORIA DELLE AZIONI EFFETTUATE
        self.logHistory = []
        
        # Limite massimo di entry nella cronologia per evitare eccessivo consumo di RAM
        self.max_logs = 100

    def logAction(self, description):
        """
        Registra un'azione con timestamp.
        Se la cronologia supera il limite, rimuove l'azione più vecchia.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {description}"
        
        self.logHistory.append(entry)
        
        # Mantiene pulita la memoria
        if len(self.logHistory) > self.max_logs:
            self.logHistory.pop(0)
            
        return entry

    def getLogs(self):
        """Restituisce lo storico come stringa pronta per la UI."""
        if not self.logHistory:
            return ""
        # Inverte l'ordine per mostrare le azioni più recenti in alto nel dialog
        return "\n".join(reversed(self.logHistory))

    def savePreset(self, name, params):
        """Salva o sovrascrive un preset con i parametri correnti."""
        try:
            data = self._readPresets()
            data[name] = params
            self._writePresets(data)
            return True
        except Exception as e:
            print(f"Errore nel salvataggio preset: {e}")
            return False

    def listPresets(self):
        """Restituisce i nomi di tutti i preset disponibili, ordinati alfabeticamente."""
        presets = self._readPresets()
        return sorted(list(presets.keys()))

    def loadPreset(self, name):
        """Carica un preset specifico se esiste."""
        return self._readPresets().get(name)

    def deletePreset(self, name):
        """Elimina un preset dal file di persistenza."""
        data = self._readPresets()
        if name not in data:
            return False

        del data[name]
        self._writePresets(data)
        return True

    # --- METODI PRIVATI PER L'ACCESSO AL FILE SYSTEM ---

    def _readPresets(self):
        """Legge il file JSON in modo sicuro gestendo casi di file mancante o corrotto."""
        if not os.path.exists(self.presetFile):
            return {}

        try:
            with open(self.presetFile, "r", encoding="utf-8") as file:
                content = file.read()
                if not content:
                    return {}
                return json.loads(content)
        except (json.JSONDecodeError, Exception) as e:
            print(f"Errore nella lettura dei preset: {e}")
            # Se il file è corrotto, restituisce un dizionario vuoto per non bloccare l'app
            return {}

    def _writePresets(self, data):
        """Scrive i preset su disco in formato leggibile (indentato)."""
        try:
            with open(self.presetFile, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Errore nella scrittura del file preset: {e}")