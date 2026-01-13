class NaturalLanguageInterpreter:
    def __init__(self):
        self.lastAttributes = []  

        self.vocabulary = {
            "bright": "brightness", "luminos": "brightness", "esposizion": "brightness", 
            "chiar": "brightness", "luc": "brightness", "sole": "brightness", 
            "illumin": "brightness", "bui": "brightness", "scur": "brightness", 
            "cup": "brightness", "ombr": "brightness",
            
            "contrast": "contrast", "marc": "contrast", "decis": "contrast", 
            "profond": "contrast", "fort": "contrast", "morb": "contrast", 
            "piatt": "contrast", "lavat": "contrast",
            
            "satur": "saturation", "viv": "saturation", "color": "saturation", 
            "acces": "saturation", "intens": "saturation", "caric": "saturation", 
            "spent": "saturation", "grig": "saturation", "desatur": "saturation",
            
            "cald": "warmth", "warm": "warmth", "giall": "warmth", "arancion": "warmth", 
            "estiv": "warmth", "calor": "warmth", "fredd": "warmth", "cold": "warmth", 
            "blu": "warmth", "ghiac": "warmth", "azzurr": "warmth",
            
            "nitid": "sharpness", "sharp": "sharpness", "dettagli": "sharpness", 
            "definit": "sharpness", "punt": "sharpness", "sfoc": "sharpness", 
            "morbidezz": "sharpness"
        }

        # Direzioni naturali delle parole
        self.default_directions = {
            "bui": -1, "scur": -1, "cup": -1, "ombr": -1, "morb": -1, "piatt": -1, 
            "lavat": -1, "spent": -1, "grig": -1, "desatur": -1, "fredd": -1, 
            "blu": -1, "ghiac": -1, "azzurr": -1, "sfoc": -1
        }

        self.intensifiers = {
            "molto": 2.2, "troppo": 2.8, "estremamente": 3.0, "super": 2.0, 
            "tantissim": 2.5, "davvero": 1.8, "poco": 0.4, "leggermente": 0.3, 
            "un po": 0.5, "appena": 0.2
        }

    def parsePrompt(self, text, currentParams):
        words = text.lower().replace(",", " ").replace("'", " ").split()
        changes = {}
        processedParams = []
        baseDelta = 0.25
        multiplier = 1.0

        for word in words:
            for key, val in self.intensifiers.items():
                if key in word:
                    multiplier = val
                    break

        if "bianco" in words and "nero" in words:
            return {"saturation": 0.0}, ["saturation"]
        if "reset" in words or "originale" in words:
            res = {p: 1.0 for p in ["brightness", "contrast", "saturation", "warmth", "sharpness"]}
            return res, list(res.keys())

        # LOGICA CORRETTA:
        # 'is_less' inverte la direzione naturale della parola.
        # 'is_more' conferma la direzione naturale della parola.
        is_more = any(w in words for w in ["più", "aumenta", "ancora", "molto", "troppo", "aggiungi"])
        is_less = any(w in words for w in ["meno", "riduci", "togli", "abbassa", "diminuisci"])
        
        found_in_text = []

        for word in words:
            for key, param in self.vocabulary.items():
                if key in word:
                    # Direzione base (es: "luce" = 1, "buio" = -1)
                    direction = self.default_directions.get(key, 1)
                    
                    # Se l'utente dice "meno", invertiamo il senso della parola
                    # Esempio: "meno buio" -> (-1) * (-1) = +1 (schiarisce)
                    if is_less:
                        direction *= -1
                    
                    # Nota: 'is_more' non serve che moltiplichi per 1, 
                    # perché la direzione è già quella naturale della parola.

                    val = currentParams.get(param, 1.0)
                    changes[param] = self._clamp(val + (baseDelta * direction * multiplier))
                    
                    if param not in processedParams:
                        processedParams.append(param)
                        found_in_text.append((param, direction))

        # 4. GESTIONE MEMORIA (per "ancora", "più", "meno" senza parametri)
        if not changes and (is_more or is_less) and self.lastAttributes:
            new_history = []
            for param, last_dir in self.lastAttributes:
                direction = last_dir
                if is_less: 
                    direction *= -1
                
                val = currentParams.get(param, 1.0)
                changes[param] = self._clamp(val + (baseDelta * direction * multiplier))
                processedParams.append(param)
                new_history.append((param, direction))
            self.lastAttributes = new_history
        elif changes:
            self.lastAttributes = found_in_text

        return changes, processedParams

    def _clamp(self, value):
        return max(0.0, min(value, 3.0))