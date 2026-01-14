import re

class NaturalLanguageInterpreter:
    def __init__(self):
        # MEMORIA DELLE ULTIME MODIFICHE PER SUPPORTARE COMANDI RELATIVI COME "ANCORA", "DI PIÙ", "DI MENO"
        self.lastAttributes = []

        # VOCABOLARIO SEMANTICO: ASSOCIA SOTTOSTRINGHE A PARAMETRI DI EDITING
        self.vocabulary = {
            # BRIGHTNESS
            "bright": "brightness", "luminos": "brightness", "esposizion": "brightness",
            "chiar": "brightness", "luc": "brightness", "sole": "brightness",
            "illumin": "brightness", "bui": "brightness", "scur": "brightness",
            "cup": "brightness", "ombr": "brightness",

            # CONTRAST
            "contrast": "contrast", "marc": "contrast", "decis": "contrast",
            "profond": "contrast", "fort": "contrast", "morb": "contrast",
            "piatt": "contrast", "lavat": "contrast",

            # SATURATION
            "satur": "saturation", "viv": "saturation", "color": "saturation",
            "acces": "saturation", "intens": "saturation", "caric": "saturation",
            "spent": "saturation", "grig": "saturation", "desatur": "saturation",

            # WARMTH
            "cald": "warmth", "warm": "warmth", "giall": "warmth",
            "arancion": "warmth", "estiv": "warmth", "calor": "warmth",
            "fredd": "warmth", "cold": "warmth", "blu": "warmth",
            "ghiac": "warmth", "azzurr": "warmth",

            # SHARPNESS
            "nitid": "sharpness", "sharp": "sharpness", "dettagli": "sharpness",
            "definit": "sharpness", "punt": "sharpness", "sfoc": "sharpness",
            "morbidezz": "sharpness"
        }

        # DIREZIONE SEMANTICA NATURALE DI ALCUNE PAROLE (NEGATIVA = DIMINUISCE)
        self.defaultDirections = {
            "bui": -1, "scur": -1, "cup": -1, "ombr": -1,
            "morb": -1, "piatt": -1, "lavat": -1,
            "spent": -1, "grig": -1, "desatur": -1,
            "fredd": -1, "blu": -1, "ghiac": -1,
            "azzurr": -1, "sfoc": -1
        }

        # MODIFICATORI DI INTENSITÀ CHE SCALANO L'EFFETTO BASE
        self.intensifiers = {
            "estremamente": 3.0,
            "troppo": 2.5,
            "molto": 2.0,
            "davvero": 1.8,
            "super": 1.7,
            "abbastanza": 1.2,
            "poco": 0.6,
            "leggermente": 0.4,
            "un po": 0.5,
            "appena": 0.3
        }

        # PAROLE CHE INDICANO AUMENTO O DIMINUZIONE
        self.moreWords = ["più", "aumenta", "aumenti", "alza", "incrementa"]
        self.lessWords = ["meno", "riduci", "abbassa", "diminuisci", "togli"]

    def parsePrompt(self, text, currentParams):
        # NORMALIZZA IL TESTO IN INGRESSO
        text = text.lower()

        # DIZIONARIO FINALE DELLE MODIFICHE DA APPLICARE
        changes = {}

        # LISTA DEI PARAMETRI MODIFICATI (PER LOG E UI)
        processedParams = []

        # STORIA LOCALE PER AGGIORNARE LA MEMORIA
        localHistory = []

        # DELTA BASE DI MODIFICA PER OGNI COMANDO
        baseDelta = 0.25

        # COMANDO DI RESET COMPLETO
        if any(word in text for word in ["reset", "originale", "predefinito"]):
            resetParams = {key: 1.0 for key in currentParams}
            return resetParams, list(resetParams.keys())

        # CONVERSIONE IN BIANCO E NERO
        if "bianco" in text and "nero" in text:
            return {"saturation": 0.0}, ["saturation"]

        # DIVIDE IL TESTO IN SEGMENTI LOGICI ("E", "MA", ",")
        segments = re.split(r"\b(e|ma|,)\b", text)

        for segment in segments:
            segment = segment.strip()
            if not segment:
                continue

            # CALCOLO DELL'INTENSITÀ LOCALE
            intensityMultiplier = 1.0
            for key, value in self.intensifiers.items():
                if key in segment:
                    intensityMultiplier = value
                    break

            # RILEVA DIREZIONE LOCALE
            hasMore = any(word in segment for word in self.moreWords)
            hasLess = any(word in segment for word in self.lessWords)

            for keyword, param in self.vocabulary.items():
                if keyword in segment:
                    # DIREZIONE BASE DEL TERMINE
                    direction = self.defaultDirections.get(keyword, 1)

                    # SE PRESENTE UN COMANDO DI DIMINUZIONE, INVERTE IL SIGNIFICATO
                    if hasLess:
                        direction *= -1

                    # CALCOLO DEL NUOVO VALORE PARTENDO DALLO STATO CORRENTE
                    currentValue = currentParams.get(param, 1.0)
                    newValue = self._clamp(
                        currentValue + baseDelta * direction * intensityMultiplier
                    )

                    # REGISTRA LA MODIFICA
                    changes[param] = newValue
                    processedParams.append(param)
                    localHistory.append((param, direction))
                    break

        # GESTIONE DELLA MEMORIA PER COMANDI RELATIVI SENZA PARAMETRO ESPLICITO
        if not changes and self.lastAttributes:
            hasMore = any(word in text for word in self.moreWords)
            hasLess = any(word in text for word in self.lessWords)

            for param, lastDirection in self.lastAttributes:
                direction = lastDirection
                if hasLess:
                    direction *= -1

                currentValue = currentParams.get(param, 1.0)
                changes[param] = self._clamp(
                    currentValue + baseDelta * direction
                )
                processedParams.append(param)

        # AGGIORNA LA MEMORIA SOLO SE CI SONO NUOVE MODIFICHE ESPLICITE
        if localHistory:
            self.lastAttributes = localHistory

        return changes, processedParams

    def _clamp(self, value):
        # LIMITA IL VALORE FINALE NELL'INTERVALLO CONSENTITO
        return max(0.0, min(3.0, value))
