from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.list import OneLineListItem, MDList
from kivymd.uix.label import MDLabel
from kivy.uix.scrollview import ScrollView
from plyer import filechooser
import os


def refreshPreviewAction(app):
    # AGGIORNA IL PREVIEW DELL'IMMAGINE NELL'UI DOPO OGNI MODIFICA
    tempPath = app.processor.saveTempResult()
    imageWidget = app.root.ids.main_image
    imageWidget.source = ""
    imageWidget.source = tempPath
    imageWidget.reload()


def openFileAction(app):
    # APRE IL FILECHOOSER PER CARICARE UN'IMMAGINE E AGGIORNA SLIDER E PREVIEW
    filePath = filechooser.open_file(
        title="Apri Immagine",
        filters=[("Immagini", "*.png", "*.jpg", "*.jpeg", "*.bmp", "*.webp", "*.tiff")]
    )

    if filePath and app.processor.loadImage(filePath[0]):
        refreshPreviewAction(app)
        app.manualMenu.syncSliders(app.processor.currentParams)
        app.utils.logAction(f"Immagine caricata: {os.path.basename(filePath[0])}")


def manualUpdateAction(app, paramKey, value):
    # APPLICA IL VALORE MODIFICATO DAGLI SLIDER AL PROCESSORE
    if not app.processor.originalImage:
        return

    app.processor.updateParam(paramKey, value)
    app.processor.applyProcessing()
    refreshPreviewAction(app)
    app.utils.logAction(f"Slider {paramKey} impostato a {value:.2f}")


def processPromptAction(app):
    # ELABORA IL TESTO INSERITO DALL'UTENTE CON L'INTERPRETER
    text = app.root.ids.prompt_input.text
    if not text or not app.processor.originalImage:
        return

    changes, paramsList = app.interpreter.parsePrompt(text, app.processor.currentParams)

    if changes:
        for param, value in changes.items():
            app.processor.updateParam(param, value)

        app.processor.applyProcessing()
        refreshPreviewAction(app)
        app.manualMenu.syncSliders(app.processor.currentParams)
        app.utils.logAction(f"Prompt: '{text}' (Modificati: {', '.join(paramsList)})")

    app.root.ids.prompt_input.text = ""


def saveFinalImageAction(app):
    # SALVA IL RISULTATO FINALE SU DISCO CON GESTIONE AUTOMATICA ESTENSIONE
    if not app.processor.processedImage:
        return

    filePath = filechooser.save_file(
        title="Salva Immagine",
        filters=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("WEBP", "*.webp"), ("TIFF", "*.tiff")]
    )

    if not filePath:
        return

    targetPath = filePath[0]
    ext = os.path.splitext(targetPath)[1].lower()

    if not ext:
        targetPath += ".png"
        ext = ".png"

    formatMap = {
        ".png": "PNG",
        ".jpg": "JPEG",
        ".jpeg": "JPEG",
        ".webp": "WEBP",
        ".tiff": "TIFF"
    }

    fmt = formatMap.get(ext, "PNG")
    app.processor.processedImage.save(targetPath, fmt)
    app.utils.logAction(f"Immagine esportata: {os.path.basename(targetPath)} ({fmt})")


def showCropMenuAction(app):
    # MOSTRA IL DIALOGO PER SCEGLIERE IL FORMATO DI RITAGLIO
    if not app.processor.originalImage:
        return

    layout = MDBoxLayout(orientation="vertical", size_hint_y=None, height="240dp")
    scroll = ScrollView()
    listView = MDList()

    cropFormats = [
        ("Originale (Reset)", "original"),
        ("1:1 Quadrato", 1.0),
        ("16:9 Panoramico", 16 / 9),
        ("4:5 Ritratto", 4 / 5),
        ("3:2 Classico", 3 / 2)
    ]

    for label, ratio in cropFormats:
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
        buttons=[MDFlatButton(text="ANNULLA", on_release=lambda x: app.dialog.dismiss())]
    )
    app.dialog.open()


def applyCropAction(app, ratio):
    # APPLICA IL RITAGLIO SCELTO E AGGIORNA PREVIEW
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
    # MOSTRA IL DIALOGO PER SALVARE UN NUOVO PRESET
    if not app.processor.originalImage:
        return

    content = MDBoxLayout(
        orientation="vertical",
        spacing="12dp",
        size_hint_y=None,
        height="80dp"
    )

    app.presetField = MDTextField(hint_text="Nome preset (es. Vintage)")
    content.add_widget(app.presetField)

    app.dialog = MDDialog(
        title="Salva Preset",
        type="custom",
        content_cls=content,
        buttons=[
            MDFlatButton(text="ANNULLA", on_release=lambda x: app.dialog.dismiss()),
            MDRaisedButton(text="SALVA", on_release=lambda x: savePresetAction(app))
        ]
    )
    app.dialog.open()


def savePresetAction(app):
    # SALVA I PARAMETRI CORRENTI COME NUOVO PRESET
    presetName = app.presetField.text
    if presetName:
        app.utils.savePreset(presetName, app.processor.currentParams)
        app.utils.logAction(f"Preset salvato: {presetName}")
    app.dialog.dismiss()


def loadPresetAction(app, presetName):
    # CARICA UN PRESET E APPLICA I PARAMETRI ALL'IMMAGINE
    app.dialog.dismiss()
    params = app.utils.loadPreset(presetName)

    if params:
        app.processor.updateParamsBatch(params)
        app.processor.applyProcessing()
        refreshPreviewAction(app)
        app.manualMenu.syncSliders(app.processor.currentParams)
        app.utils.logAction(f"Preset caricato: {presetName}")


def deletePresetAction(app, presetName):
    # ELIMINA UN PRESET E AGGIORNA LA LISTA DEI PRESET
    app.utils.deletePreset(presetName)
    app.utils.logAction(f"Preset eliminato: {presetName}")
    app.dialog.dismiss()
    showLoadPresetDialogAction(app)


def showLogDialogAction(app):
    # MOSTRA IL LOG DELLE AZIONI IN UN DIALOGO SCORRIBILE
    logs = app.utils.getLogs() or "Nessuna azione registrata in questa sessione."

    content = MDBoxLayout(orientation="vertical", size_hint_y=None, height="300dp", padding="12dp")
    scroll = ScrollView(do_scroll_x=False)

    label = MDLabel(text=logs, size_hint_y=None, halign="left", valign="top")
    label.bind(texture_size=lambda inst, val: setattr(inst, "height", val[1]))
    label.text_size = (400, None)

    scroll.add_widget(label)
    content.add_widget(scroll)

    app.dialog = MDDialog(
        title="Cronologia Azioni",
        type="custom",
        content_cls=content,
        buttons=[MDFlatButton(text="CHIUDI", on_release=lambda x: app.dialog.dismiss())]
    )
    app.dialog.open()


def undoAction(app):
    # ESEGUE UN UNDO E AGGIORNA UI E SLIDER
    if app.processor.undo():
        refreshPreviewAction(app)
        app.manualMenu.syncSliders(app.processor.currentParams)
        app.utils.logAction("Undo")


def redoAction(app):
    # ESEGUE UN REDO E AGGIORNA UI E SLIDER
    if app.processor.redo():
        refreshPreviewAction(app)
        app.manualMenu.syncSliders(app.processor.currentParams)
        app.utils.logAction("Redo")


def showLoadPresetDialogAction(app):
    # MOSTRA LA LISTA DEI PRESET DISPONIBILI E PERMETTE DI CARICARLI
    presets = app.utils.getPresetNames()

    if not presets:
        app.utils.logAction("Nessun preset disponibile")
        return

    layout = MDBoxLayout(orientation="vertical", size_hint_y=None, height="300dp", padding="12dp")
    scroll = ScrollView()
    listView = MDList()

    for name in presets:
        item = OneLineListItem(text=name, on_release=lambda x, n=name: loadPresetAction(app, n))
        listView.add_widget(item)

    scroll.add_widget(listView)
    layout.add_widget(scroll)

    app.dialog = MDDialog(
        title="Carica Preset",
        type="custom",
        content_cls=layout,
        buttons=[MDFlatButton(text="CHIUDI", on_release=lambda x: app.dialog.dismiss())]
    )
    app.dialog.open()
