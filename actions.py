from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.list import (
    OneLineListItem,
    OneLineAvatarIconListItem,
    IconRightWidget,
    MDList
)
from kivy.uix.scrollview import ScrollView
from plyer import filechooser
import os

def refreshPreviewAction(app):
    """Aggiorna l'elemento Image della UI ricaricando il file temporaneo."""
    path = app.processor.saveTempResult()
    imageWidget = app.root.ids.main_image
    imageWidget.source = ""  # Reset per forzare il refresh
    imageWidget.source = path
    imageWidget.reload()

def openFileAction(app):
    """Gestisce l'apertura di un nuovo file immagine tramite filechooser."""
    path = filechooser.open_file(
        title="Apri Immagine",
        filters=[("Immagini", "*.png", "*.jpg", "*.jpeg")]
    )

    if path and app.processor.loadImage(path[0]):
        refreshPreviewAction(app)
        app.manualMenu.syncSliders(app.processor.currentParams)
        # LOG CRONOLOGIA
        filename = os.path.basename(path[0])
        app.utils.logAction(f"Immagine caricata: {filename}")

def manualUpdateAction(app, paramKey, value):
    """Applica le modifiche provenienti dal movimento manuale degli slider."""
    if not app.processor.originalImage:
        return

    app.processor.updateParam(paramKey, value)
    app.processor.applyProcessing()
    refreshPreviewAction(app)
    # LOG CRONOLOGIA
    app.utils.logAction(f"Slider {paramKey} impostato a {value:.2f}")

def processPromptAction(app):
    """Analizza il testo inserito, aggiorna i parametri e pulisce l'input."""
    text = app.root.ids.prompt_input.text
    if not text or not app.processor.originalImage:
        return

    changes, params_list = app.interpreter.parsePrompt(text, app.processor.currentParams)

    if changes:
        for param, value in changes.items():
            app.processor.updateParam(param, value)

        app.processor.applyProcessing()
        refreshPreviewAction(app)
        app.manualMenu.syncSliders(app.processor.currentParams)
        
        # LOG CRONOLOGIA
        app.utils.logAction(f"Prompt: '{text}' (Modificati: {', '.join(params_list)})")
    
    app.root.ids.prompt_input.text = ""

def saveFinalImageAction(app):
    """Esporta l'immagine processata in formato PNG."""
    if not app.processor.processedImage:
        return

    path = filechooser.save_file(
        title="Salva Immagine",
        filters=[("PNG", "*.png")]
    )

    if path:
        target = path[0] if path[0].endswith(".png") else path[0] + ".png"
        app.processor.processedImage.save(target)
        app.utils.logAction(f"Immagine salvata in: {os.path.basename(target)}")

def showCropMenuAction(app):
    """Mostra il dialogo con le opzioni di aspect ratio per il ritaglio."""
    if not app.processor.originalImage:
        return

    layout = MDBoxLayout(orientation="vertical", size_hint_y=None, height="240dp")
    scroll = ScrollView()
    listView = MDList()

    formats = [
        ("Originale (Reset)", "original"),
        ("1:1 Quadrato", 1.0),
        ("16:9 Panoramico", 16 / 9),
        ("4:5 Ritratto", 4 / 5),
        ("3:2 Classico", 3 / 2)
    ]

    for label, ratio in formats:
        item = OneLineListItem(
            text=label,
            on_release=lambda x, r=ratio: applyCropAction(app, r)
        )
        listView.add_widget(item)

    scroll.add_widget(listView)
    layout.add_widget(scroll)

    app.dialog = MDDialog(
        title="Scegli Formato Ritaglio",
        type="custom",
        content_cls=layout,
        buttons=[
            MDFlatButton(text="ANNULLA", on_release=lambda x: app.dialog.dismiss())
        ]
    )
    app.dialog.open()

def applyCropAction(app, ratio):
    """Esegue l'operazione di ritaglio scelta dal menu."""
    app.dialog.dismiss()

    if ratio == "original":
        app.processor.workingImage = app.processor.originalImage.copy()
        app.utils.logAction("Ritaglio resettato all'originale")
    else:
        app.processor.cropFormat(ratio)
        app.utils.logAction(f"Applicato ritaglio ratio: {ratio:.2f}")

    app.processor.applyProcessing()
    refreshPreviewAction(app)

def showSavePresetDialogAction(app):
    """Mostra il dialogo per inserire il nome del nuovo preset."""
    if not app.processor.originalImage:
        return

    content = MDBoxLayout(
        orientation="vertical",
        spacing="12dp",
        size_hint_y=None,
        height="80dp"
    )

    app.presetField = MDTextField(hint_text="Inserisci nome preset (es. Vintage)")
    content.add_widget(app.presetField)

    app.dialog = MDDialog(
        title="Salva Preset Corrente",
        type="custom",
        content_cls=content,
        buttons=[
            MDFlatButton(text="ANNULLA", on_release=lambda x: app.dialog.dismiss()),
            MDRaisedButton(text="SALVA", on_release=lambda x: savePresetAction(app))
        ]
    )
    app.dialog.open()

def savePresetAction(app):
    """Salva i parametri attuali tramite UtilsManager."""
    name = app.presetField.text
    if name:
        app.utils.savePreset(name, app.processor.currentParams)
        app.utils.logAction(f"Preset salvato: {name}")
    app.dialog.dismiss()

def showLoadPresetDialogAction(app):
    """Mostra la lista dei preset salvati per il caricamento o eliminazione."""
    presets = app.utils.listPresets()

    if not presets:
        app.dialog = MDDialog(
            title="Preset Salvati",
            text="Nessun preset trovato in memoria.",
            buttons=[MDFlatButton(text="OK", on_release=lambda x: app.dialog.dismiss())]
        )
        app.dialog.open()
        return

    layout = MDBoxLayout(orientation="vertical", size_hint_y=None, height="240dp")
    scroll = ScrollView()
    listView = MDList()

    for preset in presets:
        item = OneLineAvatarIconListItem(
            text=preset,
            on_release=lambda x, p=preset: loadPresetAction(app, p)
        )

        deleteIcon = IconRightWidget(
            icon="delete",
            on_release=lambda x, p=preset: deletePresetAction(app, p)
        )

        item.add_widget(deleteIcon)
        listView.add_widget(item)

    scroll.add_widget(listView)
    layout.add_widget(scroll)

    app.dialog = MDDialog(
        title="I tuoi Preset",
        type="custom",
        content_cls=layout,
        buttons=[MDFlatButton(text="CHIUDI", on_release=lambda x: app.dialog.dismiss())]
    )
    app.dialog.open()

def loadPresetAction(app, name):
    """Applica un preset salvato e aggiorna l'interfaccia."""
    app.dialog.dismiss()
    params = app.utils.loadPreset(name)

    if params:
        for key, value in params.items():
            app.processor.updateParam(key, value)

        app.processor.applyProcessing()
        refreshPreviewAction(app)
        app.manualMenu.syncSliders(app.processor.currentParams)
        app.utils.logAction(f"Preset caricato: {name}")

def deletePresetAction(app, name):
    """Elimina un preset e ricarica la lista."""
    app.utils.deletePreset(name)
    app.utils.logAction(f"Preset eliminato: {name}")
    app.dialog.dismiss()
    showLoadPresetDialogAction(app)

def showLogDialogAction(app):
    """Mostra la cronologia testuale di tutte le azioni della sessione."""
    logs = app.utils.getLogs() or "Nessuna azione registrata in questa sessione."
    app.dialog = MDDialog(
        title="Cronologia Azioni",
        text=logs,
        buttons=[MDFlatButton(text="CHIUDI", on_release=lambda x: app.dialog.dismiss())]
    )
    app.dialog.open()