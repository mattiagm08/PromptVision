from PIL import Image, ImageEnhance
import os
import copy

class ImageEngine:
    def __init__(self):
        # IMMAGINE ORIGINALE CARICATA DALL'UTENTE
        self.originalImage = None

        # IMMAGINE IN LAVORAZIONE SU CUI APPLICARE LE MODIFICHE
        self.workingImage = None

        # IMMAGINE ELABORATA CON TUTTI GLI EFFETTI APPLICATI
        self.processedImage = None

        # RIFERIMENTO ALL'IMMAGINE ATTUALE MOSTRATA IN UI
        self.currentImage = None

        # PARAMETRI CORRENTI DI ELABORAZIONE (BRIGHTNESS, CONTRAST, ETC.)
        self.currentParams = self._defaultParams()

        # STACK PER GESTIONE UNDO/REDO
        self.undoStack = []
        self.redoStack = []

    def _defaultParams(self):
        # RESTITUISCE I PARAMETRI DI DEFAULT (VALORE NEUTRO = 1.0)
        return {
            "brightness": 1.0,
            "contrast": 1.0,
            "saturation": 1.0,
            "sharpness": 1.0,
            "warmth": 1.0
        }

    def _pushState(self):
        # MEMORIZZA LO STATO CORRENTE NELLO STACK UNDO E RESETTA REDO
        self.undoStack.append(copy.deepcopy(self.currentParams))
        self.redoStack.clear()

    def undo(self):
        # ESEGUE UN UNDO DEI PARAMETRI E APPLICA ELABORAZIONE
        if not self.undoStack:
            return False

        self.redoStack.append(copy.deepcopy(self.currentParams))
        self.currentParams = self.undoStack.pop()
        self.applyProcessing(pushState=False)
        return True

    def redo(self):
        # ESEGUE UN REDO DEI PARAMETRI E APPLICA ELABORAZIONE
        if not self.redoStack:
            return False

        self.undoStack.append(copy.deepcopy(self.currentParams))
        self.currentParams = self.redoStack.pop()
        self.applyProcessing(pushState=False)
        return True

    def loadImage(self, path):
        # CARICA L'IMMAGINE DAL DISCO E INIZIALIZZA LE IMMAGINI INTERNE
        if not os.path.exists(path):
            return False

        try:
            self.originalImage = Image.open(path).convert("RGB")
            self.workingImage = self.originalImage.copy()
            self.currentImage = self.originalImage.copy()
            self.currentParams = self._defaultParams()

            self.undoStack.clear()
            self.redoStack.clear()

            self.applyProcessing(pushState=False)
            return True
        except Exception as e:
            print(e)
            return False

    def updateParam(self, key, value):
        # AGGIORNA IL SINGOLO PARAMETRO E MEMORIZZA LO STATO PRECEDENTE
        if key in self.currentParams:
            self._pushState()
            self.currentParams[key] = value

    def cropFormat(self, ratio):
        # APPLICA IL RITAGLIO DELL'IMMAGINE IN BASE AL RAPPORTO SPECIFICATO
        if not self.workingImage:
            return

        self._pushState()

        width, height = self.workingImage.size
        currentRatio = width / height

        if currentRatio > ratio:
            # RITAGLIO ORIZZONTALE
            newWidth = int(height * ratio)
            offset = (width - newWidth) // 2
            cropBox = (offset, 0, width - offset, height)
        else:
            # RITAGLIO VERTICALE
            newHeight = int(width / ratio)
            offset = (height - newHeight) // 2
            cropBox = (0, offset, width, height - offset)

        self.workingImage = self.workingImage.crop(cropBox)
        self.applyProcessing(pushState=False)

    def applyProcessing(self, pushState=True):
        # APPLICA TUTTI GLI EFFETTI SUI PARAMETRI CORRENTI
        if not self.workingImage:
            return

        image = self.workingImage.copy()

        image = self._applySaturation(image)
        image = self._applyContrast(image)
        image = self._applyBrightness(image)
        image = self._applySharpness(image)
        image = self._applyWarmth(image)

        self.processedImage = image
        self.currentImage = image

    def _applySaturation(self, image):
        # APPLICA SATURAZIONE SULL'IMMAGINE
        value = self.currentParams["saturation"]
        return ImageEnhance.Color(image).enhance(value)

    def _applyContrast(self, image):
        # APPLICA CONTRASTO SULL'IMMAGINE
        value = self.currentParams["contrast"]
        return ImageEnhance.Contrast(image).enhance(value)

    def _applyBrightness(self, image):
        # APPLICA LUMINOSITÀ SULL'IMMAGINE
        value = self.currentParams["brightness"]
        return ImageEnhance.Brightness(image).enhance(value)

    def _applySharpness(self, image):
        # APPLICA NITIDEZZA SULL'IMMAGINE
        value = self.currentParams["sharpness"]
        return ImageEnhance.Sharpness(image).enhance(value)

    def _applyWarmth(self, image):
        # APPLICA TEMPERATURA CALDA/FREDDA SULL'IMMAGINE
        value = self.currentParams["warmth"]
        if value == 1.0:
            return image

        r, g, b = image.split()
        r = r.point(lambda i: min(255, int(i * value)))
        b = b.point(lambda i: min(255, int(i * (2.0 - value))))
        return Image.merge("RGB", (r, g, b))

    def saveTempResult(self):
        # SALVA TEMPORANEAMENTE L'IMMAGINE ELABORATA IN ASSETS/ E RESTITUISCE IL PATH
        os.makedirs("assets", exist_ok=True)
        path = "assets/temp_result.png"
        if self.processedImage:
            self.processedImage.save(path, "PNG")
        return path

    def updateParamsBatch(self, changes: dict):
        # AGGIORNA MULTIPLI PARAMETRI IN BLOCCO E MEMORIZZA STATO PRECEDENTE
        if not changes:
            return

        self._pushState()

        for key, value in changes.items():
            if key in self.currentParams:
                self.currentParams[key] = value
