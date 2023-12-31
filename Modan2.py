from PyQt5.QtWidgets import QTableWidgetItem, QMainWindow, QHeaderView, QFileDialog, QCheckBox, \
                            QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QProgressBar, QApplication, \
                            QDialog, QLineEdit, QLabel, QPushButton, QAbstractItemView, \
                            QMessageBox, QListView, QTreeWidgetItem, QToolButton, QTreeView, QFileSystemModel, \
                            QTableView, QSplitter, QRadioButton, QComboBox, QTextEdit, QAction, QMenu, QSizePolicy, \
                            QStatusBar, QBoxLayout, QGridLayout, QAbstractButton, QButtonGroup, QGroupBox, QInputDialog, \
                            QToolBar


from PyQt5 import QtGui, uic
from PyQt5.QtGui import QIcon, QColor, QPainter, QPen, QPixmap, QStandardItemModel, QStandardItem,\
                        QPainterPath, QFont, QImageReader, QPainter, QBrush, QMouseEvent, QWheelEvent, QDrag, QKeySequence
from PyQt5.QtCore import Qt, QRect, QSortFilterProxyModel, QSettings, QEvent, QRegExp, QSize, \
                         QItemSelectionModel, QDateTime, QBuffer, QIODevice, QByteArray, QPoint, QModelIndex, \
                         pyqtSignal, QThread, QMimeData

import math
from PyQt5.QtCore import pyqtSlot
import re,os,sys
from pathlib import Path
from peewee import *
import hashlib
from datetime import datetime, timezone
import requests
from PIL import Image
from PIL.ExifTags import TAGS
import time
import io
import shutil

from MdModel import *
from ModanDialogs import DatasetAnalysisDialog, ObjectDialog, ImportDatasetDialog, DatasetDialog, PreferencesDialog, \
    IMAGE_EXTENSION_LIST, MODE, MyGLWidget, ExportDatasetDialog, ObjectViewer2D, ProgressDialog

#import matplotlib
#matplotlib.use('Qt5Agg')

PROGRAM_NAME = "Modan2"
PROGRAM_VERSION = "0.0.1"

BASE_DIRECTORY = "."
DEFAULT_STORAGE_DIRECTORY = os.path.join(BASE_DIRECTORY, "data/")

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

ICON = {}
ICON['new_dataset'] = resource_path('icons/M2NewDataset_1.png')
ICON['new_object'] = resource_path('icons/M2NewObject_2.png')
ICON['import'] = resource_path('icons/M2Import_1.png')
ICON['export'] = resource_path('icons/M2Export_1.png')
ICON['analyze'] = resource_path('icons/M2Analysis_1.png')
ICON['preferences'] = resource_path('icons/M2Preferences_1.png')
ICON['about'] = resource_path('icons/M2About_1.png')
ICON['exit'] = resource_path('icons/exit.png')
ICON['Modan2'] = resource_path('icons/Modan2_2.png')
#ICON['dataset_2d'] = resource_path('icons/icons8-xlarge-icons-50.png') #  https://icons8.com
#ICON['dataset_3d'] = resource_path('icons/icons8-3d-50.png') #  https://icons8.com
#ICON['dataset_2d'] = resource_path('icons/2D_1616_1.png')
#ICON['dataset_3d'] = resource_path('icons/3D_1616_1.png')
ICON['dataset_2d'] = resource_path('icons/M2Dataset2D_3.png')
ICON['dataset_3d'] = resource_path('icons/M2Dataset3D_4.png')

class ModanMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        #self.setupUi(self)
        self.setGeometry(QRect(50, 50, 1400, 800))
        self.setWindowIcon(QIcon(resource_path('icons/Modan2_2.png')))
        self.setWindowTitle(PROGRAM_NAME)

        self.tableView = QTableView()
        self.treeView = QTreeView()

        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setIconSize(QSize(32,32))
        #self.toolbar.addAction(QIcon(resource_path('icons/open.png')), "Open", self.on_action_open_db_triggered)
        #self.toolbar.addAction(QIcon(resource_path('icons/newdb.png')), "New", self.on_action_new_db_triggered)
        #self.toolbar.addAction(QIcon(resource_path('icons/saveas.png')), "Save As", self.on_action_save_as_triggered)
        self.actionNewDataset = QAction(QIcon(resource_path(ICON['new_dataset'])), "New Dataset\tCtrl+N", self)
        self.actionNewDataset.triggered.connect(self.on_action_new_dataset_triggered)
        self.actionNewDataset.setShortcut(QKeySequence("Ctrl+N"))
        self.actionNewObject = QAction(QIcon(resource_path(ICON['new_object'])), "New Object\tCtrl+Shift+N", self)
        self.actionNewObject.triggered.connect(self.on_action_new_object_triggered)
        self.actionNewObject.setShortcut(QKeySequence("Ctrl+Shift+N"))
        self.actionImport = QAction(QIcon(resource_path(ICON['import'])), "Import\tCtrl+I", self)
        self.actionImport.triggered.connect(self.on_action_import_dataset_triggered)
        self.actionImport.setShortcut(QKeySequence("Ctrl+I"))
        self.actionExport = QAction(QIcon(resource_path(ICON['export'])), "Export\tCtrl+E", self)
        self.actionExport.triggered.connect(self.on_action_export_dataset_triggered)
        self.actionExport.setShortcut(QKeySequence("Ctrl+E"))
        self.actionAnalyze = QAction(QIcon(resource_path(ICON['analyze'])), "Analyze\tCtrl+G", self)
        self.actionAnalyze.triggered.connect(self.on_action_analyze_dataset_triggered)
        self.actionAnalyze.setShortcut(QKeySequence("Ctrl+G"))
        self.actionPreferences = QAction(QIcon(resource_path(ICON['preferences'])), "Preferences", self)
        self.actionPreferences.triggered.connect(self.on_action_edit_preferences_triggered)
        self.actionExit = QAction(QIcon(resource_path(ICON['exit'])), "Exit\tCtrl+W", self)
        self.actionExit.triggered.connect(self.on_action_exit_triggered)
        self.actionExit.setShortcut(QKeySequence("Ctrl+W"))
        self.actionAbout = QAction(QIcon(resource_path(ICON['about'])), "About\tF1", self)
        self.actionAbout.triggered.connect(self.on_action_about_triggered)
        self.actionAbout.setShortcut(QKeySequence("F1"))
        self.toolbar.addAction(self.actionNewDataset)
        self.toolbar.addAction(self.actionNewObject)
        self.toolbar.addAction(self.actionImport)
        self.toolbar.addAction(self.actionExport)
        self.toolbar.addAction(self.actionAnalyze)
        self.toolbar.addAction(self.actionPreferences)
        self.toolbar.addAction(self.actionAbout)
        self.toolbar.setIconSize(QSize(32,32))
        self.addToolBar(self.toolbar)

        self.actionExport.setDisabled(True)
        self.actionPreferences.setDisabled(True)

        self.main_menu = self.menuBar()
        self.file_menu = self.main_menu.addMenu("File")
        self.file_menu.addAction(self.actionExit)
        self.edit_menu = self.main_menu.addMenu("Edit")
        self.edit_menu.addAction(self.actionPreferences)
        self.data_menu = self.main_menu.addMenu("Data")
        self.data_menu.addAction(self.actionNewDataset)
        self.data_menu.addAction(self.actionNewObject)
        self.data_menu.addSeparator()
        self.data_menu.addAction(self.actionAnalyze)
        self.data_menu.addSeparator()
        self.data_menu.addAction(self.actionImport)
        self.data_menu.addAction(self.actionExport)
        self.help_menu = self.main_menu.addMenu("Help")
        self.help_menu.addAction(self.actionAbout)

        self.initUI()
        
        self.selected_dataset = None
        self.selected_object = None
        self.check_db()
        self.reset_views()
        self.load_dataset()
        self.m_app = QApplication.instance()
        self.read_settings()
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.analysis_dialog = None

    def on_action_open_db_triggered(self):
        pass

    def on_action_new_db_triggered(self):
        pass

    def on_action_save_as_triggered(self):
        pass

    def read_settings(self):
        self.m_app.settings = QSettings(QSettings.IniFormat, QSettings.UserScope,"DiploSoft", "Modan2")
        self.m_app.settings.beginGroup("Defaults")
        self.m_app.storage_directory = self.m_app.settings.value("Storage directory", os.path.abspath(DEFAULT_STORAGE_DIRECTORY))
        dir = self.m_app.storage_directory

    def check_db(self):
        gDatabase.connect()
        tables = gDatabase.get_tables()
        if tables:
            return
            print(tables)
        else:
            gDatabase.create_tables([MdDataset, MdObject, MdImage, ])

    '''
    def read_settings(self):
        #return
        settings = QSettings("Modan2", "Modan2")
        self.server_address = settings.value("server_address", "localhost")
        self.server_port = settings.value("server_port", "8000")
        self.data_folder = Path(settings.value("data_folder", "C:/Modan2/data"))
        #print("main window data folder:", self.data_folder)
        #print("main window server address:", self.server_address)
    def write_settings(self):
        settings = QSettings("Modan2", "Modan2")
        settings.setValue("server_address", self.server_address)
        settings.setValue("server_port", self.server_port)
        settings.setValue("data_folder", str(self.data_folder))
        #print("main window data folder:", self.data_folder)
        #print("main window server address:", self.server_address)
    '''

    def closeEvent(self, event):
        if self.analysis_dialog is not None:
            self.analysis_dialog.close()
        event.accept()

    @pyqtSlot()
    def on_action_edit_preferences_triggered(self):
        print("edit preferences")
    
    @pyqtSlot()
    def on_action_exit_triggered(self):
        self.close()

    @pyqtSlot() 
    def on_action_about_triggered(self):
        text = PROGRAM_NAME + " ver. " + PROGRAM_VERSION + "\n\n"
        text += "Morphometrics made easy\n\n"
        text += "This software is distributed under the terms of the MIT License.\n\n"
        text += "© 2023 Jikhan Jung\n"

        QMessageBox.about(self, "About", text)

        license_text = """
Modan2
Copyright 2023 Jikhan Jung

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS," WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT, OR OTHERWISE, ARISING FROM, OUT OF, OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

    @pyqtSlot()
    def on_action_analyze_dataset_triggered(self):
        if self.selected_dataset is None:
            QMessageBox.warning(self, "Warning", "No dataset selected")
            return
        prev_lm_count = -1
        for obj in self.selected_dataset.object_list:
            obj.unpack_landmark()
            lm_count = len(obj.landmark_list)
            #print("prev_lm_count:", prev_lm_count, "lm_count:", lm_count)
            if prev_lm_count != lm_count and prev_lm_count != -1:
                # show messagebox and close the window
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText("Error: landmark count is not consistent")
                msg.setWindowTitle("Error")
                msg.exec_()
                return
            prev_lm_count = lm_count
        
        self.analysis_dialog = DatasetAnalysisDialog(self,self.selected_dataset)
        self.analysis_dialog.show()

    def initUI(self):
        # add tableView and tableWidget to vertical layout
        #self.object_view_2d = LandmarkEditor(self)
        self.object_view_2d = ObjectViewer2D(self)
        self.object_view_2d.set_mode(MODE['VIEW'])
        self.object_view_3d = MyGLWidget(self)
        self.object_view = self.object_view_2d
        self.object_view_3d.hide()

        self.hsplitter = QSplitter(Qt.Horizontal)
        self.vsplitter = QSplitter(Qt.Vertical)

        self.vsplitter.addWidget(self.tableView)
        self.vsplitter.addWidget(self.object_view_2d)
        self.vsplitter.addWidget(self.object_view_3d)

        #self.treeView = MyTreeView()
        self.hsplitter.addWidget(self.treeView)
        self.hsplitter.addWidget(self.vsplitter)
        self.hsplitter.setSizes([300, 800])

        self.setCentralWidget(self.hsplitter)

        self.treeView.doubleClicked.connect(self.on_treeView_doubleClicked)
        self.treeView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableView.doubleClicked.connect(self.on_tableView_doubleClicked)
        self.tableView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        self.treeView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeView.customContextMenuRequested.connect(self.open_dataset_menu)
        self.tableView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableView.customContextMenuRequested.connect(self.open_object_menu)

    def open_object_menu(self, position):
        indexes = self.tableView.selectedIndexes()
        selected_object_list = self.get_selected_object_list()
        if len(selected_object_list) > 0:
            level = 0
            index = indexes[0]
            action_edit_object = QAction("Edit")
            action_edit_object.triggered.connect(self.on_tableView_doubleClicked)
            action_delete_object = QAction("Delete")
            action_delete_object.triggered.connect(self.on_action_delete_object_triggered)
            action_refresh_table = QAction("Reload")
            action_refresh_table.triggered.connect(self.load_object)
            action_edit_property_list = []
            if self.selected_dataset is not None and len(self.selected_dataset.propertyname_list)>0:
                
                for index, propertyname in enumerate(self.selected_dataset.propertyname_list):
                    action_edit_property_list.append(QAction("- Edit " + propertyname))
                    action_edit_property_list[-1].triggered.connect(lambda checked,index=index: self.on_edit_property(index))

            menu = QMenu()
            if len(selected_object_list) == 1:
                menu.addAction(action_edit_object)
            menu.addAction(action_delete_object)
            menu.addAction(action_refresh_table)
            if len(action_edit_property_list) > 0:
                menu.addSeparator()
                for action in action_edit_property_list:
                    menu.addAction(action)

            menu.exec_(self.tableView.viewport().mapToGlobal(position))

    def on_edit_property(self,idx):
        object_list = self.get_selected_object_list()
        if len(object_list) == 0:
            return

        for obj in object_list:
            obj.unpack_property()

        propertyname = self.selected_dataset.propertyname_list[idx]
        text, ok = QInputDialog.getText(self, 'Input Dialog', 'Enter new value for ' + propertyname, text="")


        if ok:
            total_count = len(object_list)
            current_count = 0
            self.progress_dialog = ProgressDialog()
            self.progress_dialog.setModal(True)
            label_text = "Updating {} values...".format(propertyname)
            self.progress_dialog.lbl_text.setText(label_text)
            self.progress_dialog.pb_progress.setValue(0)
            self.progress_dialog.show()

            for object in object_list:
                current_count += 1
                self.progress_dialog.pb_progress.setValue(int((current_count/float(total_count))*100))
                self.progress_dialog.update()
                QApplication.processEvents()
                #if self.progress_dialog.stop_progress:
                #    break

                object.unpack_property()
                if len(object.property_list) < idx+1:
                    while len(object.property_list) < idx+1:
                        object.property_list.append("")

                object.property_list[idx] = text
                object.pack_property()
                object.save()
            self.load_object()
            self.progress_dialog.close()

    @pyqtSlot()
    def on_action_delete_object_triggered(self):
        ret = QMessageBox.warning(self, "Warning", "Are you sure to delete the selected object?", QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.No:
            return
        
        selected_object_list = self.get_selected_object_list()
        if selected_object_list:
            for object in selected_object_list:
                object.delete_instance()
            dataset = self.selected_dataset
            self.reset_treeView()
            self.load_dataset()
            self.reset_tableView()
            self.select_dataset(dataset)

    def open_dataset_menu(self, position):
        indexes = self.treeView.selectedIndexes()
        if len(indexes) > 0:

            level = 0
            index = indexes[0]
            action_add_dataset = QAction("Add a child dataset")
            action_add_dataset.triggered.connect(self.on_action_new_dataset_triggered)
            action_add_object = QAction("Add an object")
            action_add_object.triggered.connect(self.on_action_new_object_triggered)
            action_refresh_tree = QAction("Reload")
            action_refresh_tree.triggered.connect(self.load_dataset)

            menu = QMenu()
            menu.addAction(action_add_dataset)
            menu.addAction(action_add_object)
            menu.addAction(action_refresh_tree)
            menu.exec_(self.treeView.viewport().mapToGlobal(position))


    @pyqtSlot()
    def on_action_import_dataset_triggered(self):
        self.dlg = ImportDatasetDialog(self)
        self.dlg.setModal(True)
        self.dlg.setWindowModality(Qt.ApplicationModal)
        self.dlg.exec_()
        self.load_dataset()        

    @pyqtSlot()
    def on_action_export_dataset_triggered(self):
        if self.selected_dataset is None:
            return
        self.dlg = ExportDatasetDialog(self)
        self.dlg.setModal(True)
        self.dlg.set_dataset(self.selected_dataset)
        self.dlg.setWindowModality(Qt.ApplicationModal)
        self.dlg.exec_()

    @pyqtSlot()
    def on_action_new_dataset_triggered(self):
        # open new dataset dialog
        self.dlg = DatasetDialog(self)
        self.dlg.setModal(True)
        if self.selected_dataset:
            self.dlg.set_parent_dataset( self.selected_dataset )
        else:
            self.dlg.set_parent_dataset( None )

        ret = self.dlg.exec_()
        self.load_dataset()
        self.reset_tableView()

    @pyqtSlot()
    def on_treeView_doubleClicked(self):
        self.dlg = DatasetDialog(self)
        self.dlg.setModal(True)
        self.dlg.set_dataset( self.selected_dataset )
        ret = self.dlg.exec_()
        if ret == 0:
            return
        elif ret == 1:
            if self.selected_dataset is None: #deleted
                self.load_dataset()
                self.reset_tableView()
            else:
                dataset = self.selected_dataset
                self.reset_treeView()
                self.load_dataset()
                self.reset_tableView()
                self.select_dataset(dataset)

    def select_dataset(self,dataset,node=None):
        if dataset is None:
            return
        if node is None:
            node = self.dataset_model.invisibleRootItem()   

        for i in range(node.rowCount()):
            item = node.child(i,0)
            if item.data() == dataset:
                self.treeView.setCurrentIndex(item.index())
                break
            self.select_dataset(dataset,node.child(i,0))

    @pyqtSlot()
    def on_action_new_object_triggered(self):
        # open new object dialog
        if not self.selected_dataset:
            return
        self.dlg = ObjectDialog(self)
        self.dlg.set_dataset(self.selected_dataset)
        object = MdObject()
        object.dataset = self.selected_dataset
        self.dlg.set_object(object)
        ret = self.dlg.exec_()
        if ret == 0:
            return

        dataset = self.selected_dataset
        self.load_dataset()
        self.reset_tableView()
        self.select_dataset(dataset)
        self.load_object()

    @pyqtSlot()
    def on_tableView_doubleClicked(self):
        self.dlg = ObjectDialog(self)
        self.dlg.setModal(True)
        self.dlg.set_dataset(self.selected_dataset)
        self.dlg.set_object( self.selected_object )
        self.dlg.exec_()
        dataset = self.selected_dataset
        self.reset_treeView()
        self.load_dataset()
        self.reset_tableView()
        self.select_dataset(dataset)
        self.load_object()
        self.object_view.clear_object()

    def reset_treeView(self):
        self.dataset_model = QStandardItemModel()
        self.treeView.setModel(self.dataset_model)
        self.treeView.setHeaderHidden(True)
        self.dataset_selection_model = self.treeView.selectionModel()
        self.dataset_selection_model.selectionChanged.connect(self.on_dataset_selection_changed)
        header = self.treeView.header()
        self.treeView.setSelectionBehavior(QTreeView.SelectRows)

        self.treeView.setDragEnabled(True)
        self.treeView.setAcceptDrops(True)
        self.treeView.setDropIndicatorShown(True)
        self.treeView.dropEvent = self.dropEvent

    # accept drop event
    def dropEvent(self, event):
        if event.source() == self.treeView:
            target_index=self.treeView.indexAt(event.pos())
            target_item = self.dataset_model.itemFromIndex(target_index)
            target_dataset = target_item.data()

            source_index = event.source().currentIndex()
            source_item = self.dataset_model.itemFromIndex(source_index)
            source_dataset = source_item.data()

            source_dataset.parent = target_dataset
            source_dataset.save()
            self.load_dataset()
            self.reset_tableView()

        elif event.source() == self.tableView:
            shift_clicked = False
            modifiers = QApplication.keyboardModifiers()
            if modifiers == Qt.ShiftModifier:
                shift_clicked = True

            target_index=self.treeView.indexAt(event.pos())
            target_item = self.dataset_model.itemFromIndex(target_index)
            target_dataset = target_item.data()
            #print("target_dataset",target_dataset)

            selected_object_list = self.get_selected_object_list()
            source_dataset = None
            #print("selected_object_list",selected_object_list)

            total_count = len(selected_object_list)
            current_count = 0

            self.progress_dialog = ProgressDialog()
            self.progress_dialog.setModal(True)
            if shift_clicked:
                label_text = "Moving {} objects...".format(total_count)
            else:
                label_text = "Copying {} objects...".format(total_count)
            self.progress_dialog.lbl_text.setText(label_text)
            self.progress_dialog.pb_progress.setValue(0)
            self.progress_dialog.show()


            for source_object in selected_object_list:
                current_count += 1
                self.progress_dialog.pb_progress.setValue(int((current_count/float(total_count))*100))
                self.progress_dialog.update()
                QApplication.processEvents()
                if self.progress_dialog.stop_progress:
                    break

                if source_object.dataset.dimension == target_dataset.dimension:
                    # if shift is pressed, move instead of copy
                    if shift_clicked:
                        if source_object.image.count() > 0:
                            source_image_path = source_object.image[0].get_image_path(self.m_app.storage_directory)
                        source_dataset = source_object.dataset
                        source_object.dataset = target_dataset
                        source_object.save()
                        if source_object.image.count() > 0:
                            target_image = source_object.image[0]
                            target_image_path = target_image.get_image_path(self.m_app.storage_directory)
                            if os.path.exists(source_image_path):
                                if not os.path.exists(os.path.dirname(target_image_path)):
                                    os.makedirs(os.path.dirname(target_image_path))

                                if os.path.exists(target_image_path):
                                    os.remove(target_image_path)
                                os.rename(source_image_path, target_image_path)
                    else:
                        # copy object
                        source_dataset = source_object.dataset
                        new_object = MdObject()
                        new_object.object_name = source_object.object_name
                        new_object.object_desc = source_object.object_desc
                        new_object.pixels_per_mm = source_object.pixels_per_mm
                        new_object.landmark_str = source_object.landmark_str
                        new_object.property_list = source_object.property_list
                        new_object.dataset = target_dataset
                        new_object.save()
                        if source_object.image.count() > 0:
                            old_image = source_object.image[0]
                            source_image_path = old_image.get_image_path(self.m_app.storage_directory)
                            new_image = MdImage()
                            new_image.original_path = old_image.original_path
                            new_image.original_filename = old_image.original_filename
                            new_image.name = old_image.name
                            new_image.md5hash = old_image.md5hash
                            new_image.size = old_image.size
                            new_image.exifdatetime = old_image.exifdatetime
                            new_image.file_created = old_image.file_created
                            new_image.file_modified = old_image.file_modified
                            new_image.object = new_object
                            new_image.save()
                            new_image_path = new_image.get_image_path(self.m_app.storage_directory)
                            #print(source_image_path, new_image_path)
                            if os.path.exists(source_image_path):
                                if not os.path.exists(os.path.dirname(new_image_path)):
                                    os.makedirs(os.path.dirname(new_image_path))
                                if os.path.exists(new_image_path):
                                    os.remove(new_image_path)
                                shutil.copyfile(source_image_path, new_image_path)

                else:
                    QMessageBox.warning(self, "Warning", "Dimension mismatch")
                    break
            self.progress_dialog.close()

            if source_dataset is not None:
                self.load_dataset()
                self.reset_tableView()
                self.select_dataset(source_dataset)

    def get_selected_object_list(self):
        selected_indexes = self.tableView.selectionModel().selectedRows()
        if len(selected_indexes) == 0:
            return None

        new_index_list = []
        model = selected_indexes[0].model()
        if hasattr(model, 'mapToSource'):
            for index in selected_indexes:
                new_index = model.mapToSource(index)
                new_index_list.append(new_index)
            selected_indexes = new_index_list
        
        selected_object_list = []
        for index in selected_indexes:
            item = self.object_model.itemFromIndex(index)
            object_id = item.text()
            object_id = int(object_id)
            object = MdObject.get_by_id(object_id)
            selected_object_list.append(object)

        return selected_object_list

    def reset_tableView(self):
        self.object_model = QStandardItemModel()
        header_labels = ["ID", "Name", "Count", "CSize"]
        if self.selected_dataset is not None:
            self.selected_dataset.unpack_propertyname_str()
            if self.selected_dataset.propertyname_list is not None and len( self.selected_dataset.propertyname_list ) > 0:
                header_labels.extend( self.selected_dataset.propertyname_list )
            if self.selected_dataset.dimension == 2:
                self.object_view = self.object_view_2d
                self.object_view_2d.show()
                self.object_view_3d.hide()
            else:
                #self.object_view_3d.deleteLater()
                #self.object_view_3d = MyGLWidget(self)
                self.object_view = self.object_view_3d
                #self.vsplitter.addWidget(self.object_view_3d)
                self.object_view_2d.hide()
                self.object_view_3d.show()
        self.object_model.setColumnCount(len(header_labels))
        self.object_model.setHorizontalHeaderLabels( header_labels )
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.object_model)
        self.tableView.setModel(self.proxy_model)
        self.tableView.setColumnWidth(0, 50)
        self.tableView.setColumnWidth(1, 200)
        self.tableView.setColumnWidth(2, 50)
        self.tableView.setColumnWidth(3, 50)
        header = self.tableView.horizontalHeader()    
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.tableView.verticalHeader().setDefaultSectionSize(20)
        self.tableView.verticalHeader().setVisible(False)
        self.tableView.setSelectionBehavior(QTableView.SelectRows)
        self.object_selection_model = self.tableView.selectionModel()
        self.object_selection_model.selectionChanged.connect(self.on_object_selection_changed)

        self.tableView.setDragEnabled(True)
        self.tableView.setAcceptDrops(True)
        #print("tableview accept drops:", self.tableView.acceptDrops())
        self.tableView.setDropIndicatorShown(True)
        self.tableView.dropEvent = self.tableView_drop_event
        self.tableView.dragEnterEvent = self.tableView_drag_enter_event
        self.tableView.dragMoveEvent = self.tableView_drag_move_event

        self.tableView.setSortingEnabled(True)
        self.tableView.sortByColumn(0, Qt.AscendingOrder)
        self.object_model.setSortRole(Qt.UserRole)
        self.clear_object_view()

    def tableView_drop_event(self, event):
        if self.selected_dataset is None:
            return
        file_name_list = event.mimeData().text().strip().split("\n")
        if len(file_name_list) == 0:
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        for file_name in file_name_list:
            file_name = re.sub('file:///', '', file_name)
            ext = file_name.split('.')[-1].lower()
            if ext in IMAGE_EXTENSION_LIST:
                if self.selected_dataset.dimension != 2:
                    QMessageBox.warning(self, "Warning", "Dimension mismatch.")
                    break
                object = MdObject()
                object.dataset = self.selected_dataset
                object.object_name = Path(file_name).stem
                object.save()
                img = MdImage()
                img.object = object
                img.load_file_info(file_name)
                new_filepath = img.get_image_path( self.m_app.storage_directory)
                if not os.path.exists(os.path.dirname(new_filepath)):
                    os.makedirs(os.path.dirname(new_filepath))
                shutil.copyfile(file_name, new_filepath)
                img.save()

            elif os.path.isdir(file_name):
                self.statusBar.showMessage("Cannot process directory...",2000)

            else:
                self.statusBar.showMessage("Nothing to import.",2000)

            self.load_object()

        dataset = self.selected_dataset
        self.load_dataset()
        self.reset_tableView()
        self.select_dataset(dataset)
        self.load_object()
        QApplication.restoreOverrideCursor()

    def tableView_drag_enter_event(self, event):
        event.accept()
        return
        print("drag enter",event.mimeData().text())
        file_name_list = event.mimeData().text().strip().split("\n")
        print("file name list:", file_name_list)
        ext = file_name_list[0].split('.')[-1].lower()
        print("ext:", ext)
        if ext in ['png', 'jpg', 'jpeg','bmp','gif','tif','tiff']:
            print("image file")
            print("source:", event.source())
            print("proposed action:", event.proposedAction())
            print("drop action:", event.dropAction())
            print("possible action:", int(event.possibleActions()))
            print("kinds of drop actions:", Qt.CopyAction, Qt.MoveAction, Qt.LinkAction, Qt.ActionMask, Qt.TargetMoveAction)
            #event.acceptProposedAction()
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()


    def tableView_drag_move_event(self, event):
        event.accept()
        return
        print("drag move",event.mimeData().text())
        file_name_list = event.mimeData().text().strip().split("\n")
        print("file name list:", file_name_list)
        ext = file_name_list[0].split('.')[-1].lower()
        print("ext:", ext)
        if ext in ['png', 'jpg', 'jpeg','bmp','gif','tif','tiff']:
            print("image file")
            print("source:", event.source())
            print("proposed action:", event.proposedAction())
            print("drop action:", event.dropAction())
            print("possible action:", int(event.possibleActions()))
            print("kinds of drop actions:", Qt.CopyAction, Qt.MoveAction, Qt.LinkAction, Qt.ActionMask, Qt.TargetMoveAction)
            #event.acceptProposedAction()
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()


    def reset_views(self):
        self.reset_treeView()
        self.reset_tableView()
    
    def load_dataset(self):
        self.dataset_model.clear()
        self.selected_dataset = None
        all_record = MdDataset.filter(parent=None)
        for rec in all_record:
            rec.unpack_wireframe()
            item1 = QStandardItem(rec.dataset_name + " (" + str(rec.object_list.count()) + ")")
            if rec.dimension == 2:
                item1.setIcon(QIcon(resource_path(ICON['dataset_2d'])))
            else:
                item1.setIcon(QIcon(resource_path(ICON['dataset_3d'])))
            item2 = QStandardItem(str(rec.id))
            item1.setData(rec)
            
            self.dataset_model.appendRow([item1,item2])#,item2,item3] )
            if rec.children.count() > 0:
                self.load_subdataset(item1,item1.data())
        self.treeView.expandAll()
        self.treeView.hideColumn(1)
        #self.treeView.setIconSize(QSize(16,16))

    def load_subdataset(self, parent_item, dataset):
        all_record = MdDataset.filter(parent=dataset)
        for rec in all_record:
            rec.unpack_wireframe()
            item1 = QStandardItem(rec.dataset_name + " (" + str(rec.object_list.count()) + ")")
            if rec.dimension == 2:
                item1.setIcon(QIcon(resource_path(ICON['dataset_2d']))) 
            else:
                item1.setIcon(QIcon(resource_path(ICON['dataset_3d'])))
            item2 = QStandardItem(str(rec.id))
            item1.setData(rec)
            parent_item.appendRow([item1,item2])#,item3] )
            if rec.children.count() > 0:
                self.load_subdataset(item1,item1.data())

    def on_dataset_selection_changed(self, selected, deselected):
        indexes = selected.indexes()
        #print(indexes)
        if indexes:
            self.object_model.clear()
            item1 =self.dataset_model.itemFromIndex(indexes[0])
            ds = item1.data()
            self.selected_dataset = ds
            self.load_object()

    def load_object(self):
        self.object_model.clear()
        self.reset_tableView()
        #print("load_object")
        self.clear_object_view()
        if self.selected_dataset is None:
            return

        for obj in self.selected_dataset.object_list:
            item1 = QStandardItem()
            item1.setData(obj.id,Qt.DisplayRole)
            item2 = QStandardItem(obj.object_name)
            lm_count = obj.count_landmarks()
            item3 = QStandardItem()
            item3.setData(lm_count,Qt.DisplayRole)
            item4 = QStandardItem()
            item4.setData('',Qt.DisplayRole)
            item_list = [item1,item2,item3,item4]
            if len(self.selected_dataset.propertyname_list) > 0:
                property_list = obj.unpack_property()

                for idx,prop in enumerate(self.selected_dataset.propertyname_list):
                    item = QStandardItem()
                    if idx < len(property_list):
                        item.setData(property_list[idx],Qt.DisplayRole)
                    else:
                        item.setData('',Qt.DisplayRole)
                    item_list.append(item)

            self.object_model.appendRow(item_list)

    def on_object_selection_changed(self, selected, deselected):
        selected_object_list = self.get_selected_object_list()
        if selected_object_list is None or len(selected_object_list) != 1:
            return

        object_id = selected_object_list[0].id
        #print("selected object id:", object_id)
        self.selected_object = MdObject.get_by_id(object_id)
        #print("selected object:", self.selected_object)
        self.show_object(self.selected_object)

    def show_object(self, obj):
        #print("show object")
        self.object_view.clear_object()
        self.object_view.set_object(obj)
        self.object_view.read_only = True

    def clear_object_view(self):
        self.object_view.clear_object()

if __name__ == "__main__":
    #QApplication : 프로그램을 실행시켜주는 클래스
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path('icons/Modan2_2.png')))
    #app.preferences = QSettings("Modan", "Modan2")

    #WindowClass의 인스턴스 생성
    myWindow = ModanMainWindow()

    #프로그램 화면을 보여주는 코드
    myWindow.show()

    #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()


''' 
How to make an exe file
pyinstaller --onefile --noconsole --add-data "icons/*.png;icons" --icon="icons/Modan2_2.png" Modan2.py
'''