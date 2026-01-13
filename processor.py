from PIL import Image, ImageEnhance
import os

class ImageEngine:
    def __init__(self):
        # IMMAGINE ORIGINALE CARICATA DALL’UTENTE (MAI MODIFICATA)
        self.originalImage = None

        # IMMAGINE BASE SU CUI APPLICARE FILTRI (DOPO CROP O RESET)
        self.workingImage = None

        # RISULTATO FINALE DOPO L’APPLICAZIONE DEI PARAMETRI
        self.processedImage = None

        # IMMAGINE CHE CONTIENE LO STATO FILTRATO CORRENTE (per preview interna)
        self.currentImage = None

        # STATO CENTRALIZZATO DEI PARAMETRI DI EDITING
        self.currentParams = self._defaultParams()

        # CRONOLOGIA DEGLI STATI (Necessaria per log e funzioni di annullamento)
        self.history = []

    def _defaultParams(self):
        # VALORI STANDARD PER TUTTI I PARAMETRI
        return {
            "brightness": 1.0,
            "contrast": 1.0,
            "saturation": 1.0,
            "sharpness": 1.0,
            "warmth": 1.0
        }

    def loadImage(self, path):
        # CARICA L’IMMAGINE E RESETTA LO STATO
        if not os.path.exists(path):
            return False

        try:
            self.originalImage = Image.open(path).convert("RGB")
            self.workingImage = self.originalImage.copy()
            self.currentImage = self.originalImage.copy()
            self.currentParams = self._defaultParams()
            self.history = [] # Reset cronologia per la nuova immagine
            
            self.applyProcessing()
            return True
        except Exception as e:
            print(f"Errore nel caricamento immagine: {e}")
            return False

    def updateParam(self, key, value):
        # AGGIORNA UN PARAMETRO SE ESISTE
        if key in self.currentParams:
            self.currentParams[key] = value

    def cropFormat(self, ratio):
        # CROP CENTRALE MANTENENDO L’ASPECT RATIO DESIDERATO
        if not self.workingImage:
            return

        width, height = self.workingImage.size
        currentRatio = width / height

        if currentRatio > ratio:
            # Immagine troppo larga
            newWidth = int(height * ratio)
            offset = (width - newWidth) // 2
            cropBox = (offset, 0, width - offset, height)
        else:
            # Immagine troppo alta
            newHeight = int(width / ratio)
            offset = (height - newHeight) // 2
            cropBox = (0, offset, width, height - offset)

        self.workingImage = self.workingImage.crop(cropBox)
        self.applyProcessing() 

    def applyProcessing(self):
        # PIPELINE NON DISTRUTTIVA: parte sempre dalla workingImage originale
        if not self.workingImage:
            return

        # Crea una copia della base su cui lavorare
        image = self.workingImage.copy() 

        # Applicazione sequenziale dei filtri
        image = self._applySaturation(image)
        image = self._applyContrast(image)
        image = self._applyBrightness(image)
        image = self._applySharpness(image)
        image = self._applyWarmth(image)

        self.processedImage = image
        self.currentImage = image 

        # Registra lo stato attuale nella cronologia interna
        self.history.append({
            "params": self.currentParams.copy(),
            "image_size": self.processedImage.size
        })

    # --- METODI PRIVATI PER L'APPLICAZIONE DEI FILTRI (Utilizzano Pillow) ---
    
    def _applySaturation(self, image):
        value = self.currentParams["saturation"]
        if value != 1.0:
            return ImageEnhance.Color(image).enhance(value)
        return image

    def _applyContrast(self, image):
        value = self.currentParams["contrast"]
        if value != 1.0:
            return ImageEnhance.Contrast(image).enhance(value)
        return image

    def _applyBrightness(self, image):
        value = self.currentParams["brightness"]
        if value != 1.0:
            return ImageEnhance.Brightness(image).enhance(value)
        return image

    def _applySharpness(self, image):
        value = self.currentParams["sharpness"]
        if value != 1.0:
            return ImageEnhance.Sharpness(image).enhance(value)
        return image

    def _applyWarmth(self, image):
        value = self.currentParams["warmth"]
        if value == 1.0:
            return image

        # Split dei canali per manipolare la temperatura colore
        r, g, b = image.split()
        # Aumenta il Rosso (caldo) e diminuisce il Blu (freddo) o viceversa
        r = r.point(lambda i: min(255, max(0, int(i * value))))
        b = b.point(lambda i: min(255, max(0, int(i * (2.0 - value)))))
        return Image.merge("RGB", (r, g, b))

    def saveTempResult(self):
        # SALVA UN FILE TEMPORANEO PER IL WIDGET IMAGE DI KIVY
        os.makedirs("assets", exist_ok=True)
        path = "assets/temp_result.png"
        if self.processedImage:
            # Usiamo PNG per mantenere la massima qualità durante l'editing
            self.processedImage.save(path, "PNG")
        return path