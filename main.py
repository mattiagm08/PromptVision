from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.properties import StringProperty

# IMPORTAZIONE AZIONI UI E LOGICA DI BUSINESS (SEPARAZIONE MVC)
from actions import (
    undoAction, redoAction, openFileAction, manualUpdateAction,
    processPromptAction, saveFinalImageAction, showCropMenuAction,
    showSavePresetDialogAction, showLoadPresetDialogAction, showLogDialogAction
)

# IMPORTAZIONE MOTORI: NLP, PROCESSING IMMAGINI E UTILITY
from interpreter import NaturalLanguageInterpreter
from processor import ImageEngine
from utils import UtilsManager


class ControlRow(MDBoxLayout):
    """WIDGET RIGA SINGOLA: ICONA, LABEL, SLIDER E VALORE"""
    label_text = StringProperty("")
    icon_name = StringProperty("")


class ManualEditMenu(MDBoxLayout):
    """GESTORE DEGLI SLIDER: COSTRUZIONE DINAMICA E SINCRONIZZAZIONE"""
    
    def __init__(self, updateCallback, **kwargs):
        super().__init__(**kwargs)
        self.updateCallback = updateCallback
        self.sliders = {}  # CACHE PER AGGIORNAMENTI FUTURI
        self._buildControls()

    def _buildControls(self):
        # CONFIGURAZIONE SLIDER: (ETICHETTA, CHIAVE PARAMETRO, ICONA)
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

            # RECUPERO WIDGET DAL KV PER IL BINDING
            slider = row.ids.slider
            valueLabel = row.ids.valLabel

            # BINDING: AGGIORNA LABEL LIVE, APPLICA MODIFICA SOLO AL RILASCIO (ON_TOUCH_UP)
            slider.bind(value=lambda inst, val, lbl=valueLabel: self._updateLabel(val, lbl))
            slider.bind(on_touch_up=lambda inst, touch, k=key: self._onRelease(inst, touch, k))

            self.sliders[key] = {"slider": slider, "label": valueLabel}
            self.add_widget(row)

    def _updateLabel(self, value, label):
        # AGGIORNAMENTO VISIVO DEL VALORE (INT)
        label.text = str(int(value))

    def _onRelease(self, slider, touch, paramKey):
        # APPLICA LA MODIFICA AL PROCESSORE SOLO SE IL TOUCH È SULLO SLIDER
        if slider.collide_point(*touch.pos):
            # NORMALIZZAZIONE VALORE (0-150 -> 0.0-3.0) E CALLBACK
            self.updateCallback(paramKey, slider.value / 50.0)

    def syncSliders(self, params):
        # SINCRONIZZA GUI CON I PARAMETRI REALI (ES. DOPO UN PRESET O UNDO)
        for key, value in params.items():
            if key in self.sliders:
                sliderValue = int(value * 50)
                self.sliders[key]["slider"].value = sliderValue
                self.sliders[key]["label"].text = str(sliderValue)


class PromptVisionApp(MDApp):
    """CONTROLLER PRINCIPALE: INIZIALIZZAZIONE E ROUTING EVENTI"""
    dialog = None

    def build(self):
        # SETUP TEMA (DARK/PURPLE) E INIZIALIZZAZIONE CORE LOGICO
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.accent_palette = "Amber"

        self.processor = ImageEngine()
        self.interpreter = NaturalLanguageInterpreter()
        self.utils = UtilsManager()

        return self.root

    def on_start(self):
        # INIEZIONE DEL MENU MANUALE NELLA GUI AL LANCIO
        self.manualMenu = ManualEditMenu(updateCallback=self._manualUpdate)
        if 'sideScroll' in self.root.ids:
            self.root.ids.sideScroll.add_widget(self.manualMenu)

    # --- WRAPPER EVENTI UI -> ACTIONS ---

    def openFileManager(self):
        # APERTURA FILE CHOOSER
        openFileAction(self)

    def _manualUpdate(self, paramKey, value):
        # PONTE TRA SLIDER E PROCESSORE
        manualUpdateAction(self, paramKey, value)

    def processPrompt(self):
        # ELABORAZIONE TESTO UTENTE (NLP)
        processPromptAction(self)

    def saveFinalImage(self):
        # SALVATAGGIO SU DISCO
        saveFinalImageAction(self)

    def showCropMenu(self):
        # ATTIVAZIONE MODALITÀ RITAGLIO
        showCropMenuAction(self)

    def showSavePresetDialog(self):
        # DIALOGO SALVATAGGIO PRESET
        showSavePresetDialogAction(self)

    def showLoadPresetDialog(self):
        # DIALOGO CARICAMENTO PRESET
        showLoadPresetDialogAction(self)

    def showLogDialog(self):
        # VISUALIZZAZIONE STORICO OPERAZIONI
        showLogDialogAction(self)

    def undo(self):
        # ANNULLA AZIONE
        undoAction(self)

    def redo(self):
        # RIPRISTINA AZIONE
        redoAction(self)


if __name__ == "__main__":
    PromptVisionApp().run()