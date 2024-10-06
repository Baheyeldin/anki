
# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from __future__ import annotations

import os
import re
import time
from concurrent.futures import Future

import aqt
import aqt.forms
import aqt.main
from anki import hooks
from anki.cards import CardId
from anki.decks import DeckId
from anki.exporting import Exporter, exporters
from aqt import gui_hooks
from aqt.errors import show_exception
from aqt.qt import *
from aqt.utils import (
    checkInvalidFilename,
    disable_help_button,
    getSaveFile,
    showWarning,
    tooltip,
    tr,
)

class ExportDialog(QDialog):
    def __init__(
        self,
        mw: aqt.main.AnkiQt,
        did: DeckId | None = None,
        cids: list[CardId] | None = None,
        parent: QWidget | None = None,
    ):
        QDialog.__init__(self, parent or mw, Qt.WindowType.Window)
        self.mw = mw
        self.col = mw.col.weakref()
        self.frm = aqt.forms.exporting.Ui_ExportDialog()
        self.frm.setupUi(self)
        self.frm.legacy_support.setVisible(False)
        self.exporter: Exporter | None = None
        self.cids = cids
        disable_help_button(self)
        self.setup(did)
        self.exec()

    def setup(self, did: DeckId | None) -> None:
        self.exporters = exporters(self.col)
        idx = 0
        if did or self.cids:
            for c, (k, e) in enumerate(self.exporters):
                if e.ext == ".apkg":
                    idx = c
                    break
        self.frm.format.insertItems(0, [e[0] for e in self.exporters])
        self.frm.format.setCurrentIndex(idx)
        qconnect(self.frm.format.activated, self.exporterChanged)
        self.exporterChanged(idx)
        if self.cids is None:
            self.decks = [tr.exporting_all_decks()]
            self.decks.extend(d.name for d in self.mw.col.decks.all_names_and_ids())
            self.frm.deckList.addItems(self.decks)
            self.frm.deckList.setCurrentIndex(0)
        else:
            self.frm.deckList.hide()

    def exporterChanged(self, idx: int) -> None:
        self.exporter = self.exporters[idx][1](self.col)
        self.frm.label.setText(self.exporter.key)
        if self.cids:
            self.exporter.setCids(self.cids)
        self.frm.legacy_support.setVisible(self.exporter.requiresLegacySupport())
    
    # Override the export function to disable it
    def accept(self):
        # Disable exporting by preventing the method from executing
        showWarning("Exporting has been disabled in this version.")
        return

