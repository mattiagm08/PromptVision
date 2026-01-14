import json
import os
from datetime import datetime

class UtilsManager:
    """
    GESTISCE LA PERSISTENZA DEI DATI (PRESET) E LA REGISTRAZIONE DELLE ATTIVITÀ DURANTE LA SESSIONE
    """
    def __init__(self):
        # FILE LOCALE PER LA PERSISTENZA DEI PRESET
        self.presetFile = "presets.json"

        # STORICO IN MEMORIA DELLE AZIONI EFFETTUATE
        self.logHistory = []

        # LIMITE MASSIMO DI ENTRY NELLA CRONOLOGIA PER EVITARE ECCESSIVO CONSUMO DI RAM
        self.maxLogs = 100

    def logAction(self, description):
        """
        REGISTRA UN'AZIONE CON TIMESTAMP
        SE LA CRONOLOGIA SUPERA IL LIMITE, RIMUOVE L'AZIONE PIÙ VECCHIA
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {description}"

        self.logHistory.append(entry)

        # MANTIENE PULITA LA MEMORIA
        if len(self.logHistory) > self.maxLogs:
            self.logHistory.pop(0)

        return entry

    def getLogs(self):
        """
        RESTITUISCE LO STORICO COME STRINGA PRONTA PER LA UI
        LE AZIONI PIÙ RECENTI SONO IN ALTO
        """
        if not self.logHistory:
            return ""
        return "\n".join(reversed(self.logHistory))

    def savePreset(self, name, params):
        """
        SALVA O SOVRASCRIVE UN PRESET CON I PARAMETRI CORRENTI
        """
        try:
            data = self._readPresets()
            data[name] = params
            self._writePresets(data)
            return True
        except Exception as e:
            print(f"ERRORE NEL SALVATAGGIO PRESET: {e}")
            return False

    def getPresetNames(self):
        """
        RESTITUISCE I NOMI DI TUTTI I PRESET DISPONIBILI, ORDINATI ALFABETICAMENTE
        """
        presets = self._readPresets()
        return sorted(list(presets.keys()))

    def loadPreset(self, name):
        """
        CARICA UN PRESET SPECIFICO SE ESISTE
        """
        return self._readPresets().get(name)

    def deletePreset(self, name):
        """
        ELIMINA UN PRESET DAL FILE DI PERSISTENZA
        """
        data = self._readPresets()
        if name not in data:
            return False

        del data[name]
        self._writePresets(data)
        return True

    # --- METODI PRIVATI PER L'ACCESSO AL FILE SYSTEM ---

    def _readPresets(self):
        """
        LEGGE IL FILE JSON IN MODO SICURO, GESTENDO CASI DI FILE MANCANTE O CORROTTO
        """
        if not os.path.exists(self.presetFile):
            return {}

        try:
            with open(self.presetFile, "r", encoding="utf-8") as file:
                content = file.read()
                if not content:
                    return {}
                return json.loads(content)
        except (json.JSONDecodeError, Exception) as e:
            print(f"ERRORE NELLA LETTURA DEI PRESET: {e}")
            # SE IL FILE È CORROTTO, RESTITUISCE DIZIONARIO VUOTO PER NON BLOCCARE L'APP
            return {}

    def _writePresets(self, data):
        """
        SCRIVE I PRESET SU DISCO IN FORMATO LEGGIBILE (INDENTATO)
        """
        try:
            with open(self.presetFile, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"ERRORE NELLA SCRITTURA DEL FILE PRESET: {e}")
