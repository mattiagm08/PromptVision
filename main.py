from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.properties import StringProperty

from interpreter import NaturalLanguageInterpreter
from processor import ImageEngine
from utils import UtilsManager
from actions import (
    openFileAction,
    manualUpdateAction,
    processPromptAction,
    saveFinalImageAction,
    showCropMenuAction,
    showSavePresetDialogAction,
    showLoadPresetDialogAction,
    showLogDialogAction
)

class ControlRow(MDBoxLayout):
    """
    Rappresenta una singola riga nel menu laterale.
    Contiene l'icona, il nome del parametro, lo slider e l'etichetta del valore.
    I widget interni sono referenziati tramite ID definiti nel file .kv.
    """
    label_text = StringProperty("")
    icon_name = StringProperty("")

class ManualEditMenu(MDBoxLayout):
    """
    Menu laterale per il controllo manuale dei parametri di editing.
    Gestisce la creazione dinamica degli slider e la loro sincronizzazione.
    """
    def __init__(self, updateCallback, **kwargs):
        super().__init__(**kwargs)
        self.updateCallback = updateCallback
        self.sliders = {}
        self._buildControls()

    def _buildControls(self):
        """Definisce e aggiunge i controlli per ogni parametro supportato."""
        # Configurazione: (Etichetta UI, Chiave Parametro, Icona MD)
        controls = [
            ("ESPOSIZIONE", "brightness", "brightness-6"),
            ("CONTRASTO", "contrast", "contrast-circle"),
            ("SATURAZIONE", "saturation", "palette"),
            ("TEMPERATURA", "warmth", "thermometer"),
            ("NITIDEZZA", "sharpness", "details")
        ]

        for label, key, icon in controls:
            row = ControlRow()
            row.label_text = label
            row.icon_name = icon

            # Otteniamo i riferimenti dai widget del file .kv
            slider = row.ids.slider
            valueLabel = row.ids.valLabel

            # Bind per aggiornare l'etichetta numerica mentre si trascina
            slider.bind(
                value=lambda inst, val, lbl=valueLabel: self._updateLabel(val, lbl)
            )
            
            # Bind per applicare la modifica all'immagine solo quando si rilascia il tocco
            slider.bind(
                on_touch_up=lambda inst, touch, k=key: self._onRelease(inst, touch, k)
            )

            # Memorizziamo i riferimenti per poterli sincronizzare in seguito
            self.sliders[key] = {"slider": slider, "label": valueLabel}
            self.add_widget(row)

    def _updateLabel(self, value, label):
        """Aggiorna il testo del valore accanto allo slider (0-100)."""
        label.text = str(int(value))

    def _onRelease(self, slider, touch, paramKey):
        """Invia il nuovo valore al processore solo al termine dell'interazione."""
        if slider.collide_point(*touch.pos):
            # Convertiamo il valore dello slider (0-150) in scala (0.0-3.0)
            # 50 è il valore neutro (1.0)
            self.updateCallback(paramKey, slider.value / 50.0)

    def syncSliders(self, params):
        """Sincronizza la posizione degli slider con i parametri correnti (es. dopo un prompt)."""
        for key, value in params.items():
            if key in self.sliders:
                # Convertiamo da scala decimale a valore slider
                sliderValue = int(value * 50)
                self.sliders[key]["slider"].value = sliderValue
                self.sliders[key]["label"].text = str(sliderValue)

class PromptVisionApp(MDApp):
    """
    Classe principale dell'applicazione PromptVision.
    Inizializza i motori logici e gestisce gli eventi della UI.
    """
    dialog = None

    def build(self):
        # Configurazione estetica
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.accent_palette = "Amber"

        # Inizializzazione componenti logici
        self.processor = ImageEngine()
        self.interpreter = NaturalLanguageInterpreter()
        self.utils = UtilsManager()

        # Il file .kv viene caricato automaticamente se ha lo stesso nome (promptvision.kv)
        # o se definito esplicitamente nel metodo build.
        return self.root

    def on_start(self):
        """Eseguito all'avvio: popola il contenitore degli slider."""
        self.manualMenu = ManualEditMenu(updateCallback=self._manualUpdate)
        # Assicurati che l'ID 'sideScroll' esista nel tuo file .kv
        if 'sideScroll' in self.root.ids:
            self.root.ids.sideScroll.add_widget(self.manualMenu)

    # --- Wrapper per le azioni (chiamate dai bottoni della UI) ---

    def openFileManager(self):
        """Apre il selettore file per caricare un'immagine."""
        openFileAction(self)

    def _manualUpdate(self, paramKey, value):
        """Gestisce l'aggiornamento proveniente dagli slider."""
        manualUpdateAction(self, paramKey, value)

    def processPrompt(self):
        """Esegue l'analisi del linguaggio naturale sul testo inserito."""
        processPromptAction(self)

    def saveFinalImage(self):
        """Salva il risultato finale su disco."""
        saveFinalImageAction(self)

    def showCropMenu(self):
        """Mostra le opzioni di ritaglio."""
        showCropMenuAction(self)

    def showSavePresetDialog(self):
        """Apre il dialogo per salvare un nuovo preset."""
        showSavePresetDialogAction(self)

    def showLoadPresetDialog(self):
        """Apre il manager dei preset salvati."""
        showLoadPresetDialogAction(self)

    def showLogDialog(self):
        """Mostra la cronologia delle azioni effettuate."""
        showLogDialogAction(self)

if __name__ == "__main__":
    # Avvio dell'applicazione
    PromptVisionApp().run()