from PyQt5.QtWidgets import QTableWidgetItem, QMainWindow, QHeaderView, QFileDialog, QCheckBox, \
                            QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QProgressBar, QApplication, \
                            QDialog, QLineEdit, QLabel, QPushButton, QAbstractItemView, \
                            QMessageBox, QListView, QTreeWidgetItem, QToolButton, QTreeView, QFileSystemModel, \
                            QTableView, QSplitter, QRadioButton, QComboBox, QTextEdit, QAction, QMenu, QSizePolicy, \
                            QTableWidget, QBoxLayout, QGridLayout, QAbstractButton, QButtonGroup


from PyQt5 import QtGui, uic
from PyQt5.QtGui import QIcon, QColor, QPainter, QPen, QPixmap, QStandardItemModel, QStandardItem,\
                        QPainterPath, QFont, QImageReader, QPainter, QBrush, QMouseEvent, QWheelEvent
from PyQt5.QtCore import Qt, QRect, QSortFilterProxyModel, QSettings, QEvent, QRegExp, QSize, \
                         QItemSelectionModel, QDateTime, QBuffer, QIODevice, QByteArray, QPoint, QModelIndex, \
                         pyqtSignal, QThread


from PyQt5.QtCore import pyqtSlot
import re,os,sys
from pathlib import Path
from peewee import *
import hashlib
from datetime import datetime, timezone
import requests
from PIL import Image
from PIL.ExifTags import TAGS
#import imagesize
#from datetime import datetime
import time
import io

PROGRAM_NAME = "Modan2"
PROGRAM_VERSION = "0.0.1"

from MdModel import *

class ImportDatasetDialog(QDialog):
    # NewDatasetDialog shows new dataset dialog.
    def __init__(self,parent):
        super().__init__()
        self.setWindowTitle("Import Dataset")
        self.parent = parent
        #print(self.parent.pos())
        self.setGeometry(QRect(100, 100, 600, 400))
        self.move(self.parent.pos()+QPoint(100,100))

        # add file open dialog
        self.btnOpenFile = QPushButton("Open File")
        self.btnOpenFile.clicked.connect(self.open_file)
        self.edtFilename = QLineEdit()
        self.edtFilename.setReadOnly(True)
        self.edtFilename.setText("")
        self.edtFilename.setPlaceholderText("Select a file to import")
        self.edtFilename.setMinimumWidth(400)
        self.edtFilename.setMaximumWidth(400)
        self.edtFilename.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # add file type combo box
        self.cbxFileType = QComboBox()
        self.cbxFileType.addItem("TPS")
        self.cbxFileType.addItem("X1Y1")
        self.cbxFileType.addItem("Morphologika")
        self.cbxFileType.addItem("Landmark")
        self.cbxFileType.addItem("Image")
        self.cbxFileType.addItem("Other")
        self.cbxFileType.currentIndexChanged.connect(self.file_type_changed)

        # add dataset name edit
        self.edtDatasetName = QLineEdit()
        self.edtDatasetName.setText("")
        self.edtDatasetName.setPlaceholderText("Dataset Name")
        self.edtDatasetName.setMinimumWidth(400)
        self.edtDatasetName.setMaximumWidth(400)
        self.edtDatasetName.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                
        # add object count edit
        self.edtObjectCount = QLineEdit()
        self.edtObjectCount.setReadOnly(True)
        self.edtObjectCount.setText("")
        self.edtObjectCount.setPlaceholderText("Object Count")
        self.edtObjectCount.setMinimumWidth(100)
        self.edtObjectCount.setMaximumWidth(100)
        self.edtObjectCount.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.btnImport = QPushButton("Excute Import")
        self.btnImport.clicked.connect(self.import_file)
        self.btnImport.setEnabled(False)

        # add progress bar
        self.prgImport = QProgressBar()
        self.prgImport.setMinimum(0)
        self.prgImport.setMaximum(100)
        self.prgImport.setValue(0)
        self.prgImport.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # add layout
        self.main_layout = QFormLayout()
        self.setLayout(self.main_layout)
        self.main_layout.addRow("File", self.btnOpenFile)
        self.main_layout.addRow("File Type", self.cbxFileType)
        self.main_layout.addRow("Dataset Name", self.edtDatasetName)
        self.main_layout.addRow("Object Count", self.edtObjectCount)
        self.main_layout.addRow("Import", self.btnImport)
        self.main_layout.addRow("Progress", self.prgImport)

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*.*)")
        if filename:
            self.edtFilename.setText(filename)
            self.btnImport.setEnabled(True)
            self.edtDatasetName.setText(Path(filename).stem)
            self.edtObjectCount.setText("")
            self.prgImport.setValue(0)
    
    def file_type_changed(self):
        if self.cbxFileType.currentText() == "Image":
            self.edtObjectCount.setReadOnly(False)
        else:
            self.edtObjectCount.setReadOnly(True)
            self.edtObjectCount.setText("")

    def import_file(self):
        self.btnImport.setEnabled(False)
        self.prgImport.setValue(0)
        self.prgImport.setFormat("Importing...")
        self.prgImport.update()
        self.prgImport.repaint()
        self.import_thread = ImportThread(self)
        self.import_thread.start()
        self.import_thread.finished.connect(self.import_finished)
        self.import_thread.progress.connect(self.import_progress)

    def import_finished(self):
        self.btnImport.setEnabled(True)
        self.prgImport.setValue(100)
        self.prgImport.setFormat("Import Finished")
        self.prgImport.update()
        self.prgImport.repaint()
        self.import_thread.quit()
        self.import_thread.wait()

    def import_progress(self, value):
        self.prgImport.setValue(value)
        self.prgImport.update()
        self.prgImport.repaint()

class ImportThread(QThread):

    progress = pyqtSignal(int)
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

    def run(self):
        filename = self.parent.edtFilename.text()
        filetype = self.parent.cbxFileType.currentText()
        datasetname = self.parent.edtDatasetName.text()
        objectcount = self.parent.edtObjectCount.text()
        if filetype == "TPS":
            self.import_tps(filename, datasetname)
        elif filetype == "X1Y1":
            self.import_x1y1(filename, datasetname)
        elif filetype == "Morphologika":
            self.import_morphologika(filename, datasetname)
        else:
            self.progress.emit(0)
            return
        self.progress.emit(100)

    def import_tps(self, filename, datasetname):
        # read tps file
        tps = TPS(filename)
        # create dataset
        dataset = Dataset(datasetname)
        # add landmarks
        for i in range(tps.nlandmarks):
            landmark = Landmark(tps.landmarks[i,0], tps.landmarks[i,1], tps.landmarks[i,2])
            dataset.landmarks.append(landmark)
        # add objects
        for i in range(tps.nobjects):
            object = Object()
            object.name = tps.objectnames[i]
            object.landmarks = []
            for j in range(tps.nlandmarks):
                object.landmarks.append(tps.objects[i,j,:])
            dataset.objects.append(object)
        # add dataset to project
        self.parent.parent.project.datasets.append(dataset)
        self.parent.parent.project.current_dataset = dataset

    def import_x1y1(self, filename, datasetname):
        # read x1y1 file
        x1y1 = X1Y1(filename)
        # create dataset
        dataset = MdDataset(datasetname)
        # add landmarks
        for i in range(x1y1.nlandmarks):
            landmark = Landmark(x1y1.landmarks[i,0], x1y1.landmarks[i,1], x1y1.landmarks[i,2])
            dataset
        # add objects
        for i in range(x1y1.nobjects):
            object = MdObject()
            object.name = x1y1.objectnames[i]
            object.landmarks = []
            for j in range(x1y1.nlandmarks):
                object.landmarks.append(x1y1.objects[i,j,:])
            dataset.objects.append(object)
        # add dataset to project
        self.parent.parent.project.datasets.append(dataset)
        self.parent.parent.project.current_dataset = dataset

class DatasetDialog(QDialog):
    # NewDatasetDialog shows new dataset dialog.
    def __init__(self,parent):
        super().__init__()
        self.setWindowTitle("Dataset")
        self.parent = parent
        #print(self.parent.pos())
        self.setGeometry(QRect(100, 100, 600, 400))
        self.move(self.parent.pos()+QPoint(100,100))

        self.cbxParent = QComboBox()
        self.edtDatasetName = QLineEdit()
        self.edtDatasetDesc = QLineEdit()

        self.rbtn2D = QRadioButton("2D")
        self.rbtn2D.setChecked(True)
        self.rbtn3D = QRadioButton("3D")
        dim_layout = QHBoxLayout()
        dim_layout.addWidget(self.rbtn2D)
        dim_layout.addWidget(self.rbtn3D)

        self.edtWireframe = QTextEdit()
        self.edtBaseline = QLineEdit()
        self.edtPolygons = QTextEdit()
        self.edtPropertyNameList = QTextEdit()

        self.main_layout = QFormLayout()
        self.setLayout(self.main_layout)
        self.main_layout.addRow("Parent", self.cbxParent)
        self.main_layout.addRow("Dataset Name", self.edtDatasetName)
        self.main_layout.addRow("Description", self.edtDatasetDesc)
        self.main_layout.addRow("Dimension", dim_layout)
        self.main_layout.addRow("Wireframe", self.edtWireframe)
        self.main_layout.addRow("Baseline", self.edtBaseline)
        self.main_layout.addRow("Polygons", self.edtPolygons)
        self.main_layout.addRow("Property Name List", self.edtPropertyNameList)


        self.btnOkay = QPushButton()
        self.btnOkay.setText("Save")
        self.btnOkay.clicked.connect(self.Okay)

        self.btnDelete = QPushButton()
        self.btnDelete.setText("Delete")
        self.btnDelete.clicked.connect(self.Delete)

        self.btnCancel = QPushButton()
        self.btnCancel.setText("Cancel")
        self.btnCancel.clicked.connect(self.Cancel)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btnOkay)
        btn_layout.addWidget(self.btnDelete)
        btn_layout.addWidget(self.btnCancel)
        self.main_layout.addRow(btn_layout)


        self.dataset = None
        self.load_parent_dataset()

        #self.edtDataFolder.setText(str(self.data_folder.resolve()))
        #self.edtServerAddress.setText(self.server_address)
        #self.edtServerPort.setText(self.server_port)

    def load_parent_dataset(self,curr_dataset_id = None):
        self.cbxParent.clear()
        datasets = MdDataset.select()
        for dataset in datasets:
            if curr_dataset_id is None or dataset.id != curr_dataset_id:
                self.cbxParent.addItem(dataset.dataset_name, dataset.id)

    def read_dataset(self, dataset_id):
        try:
            dataset = MdDataset.get(dataset.id == dataset_id)
        except:
            dataset = None
        self.dataset = dataset
        #self
        #return dataset

    def set_dataset(self, dataset):
        if dataset is None:
            self.dataset = None
            self.cbxParent.setCurrentIndex(-1)
            return

        self.dataset = dataset
        self.load_parent_dataset(dataset.id)
        self.cbxParent.setCurrentIndex(self.cbxParent.findData(dataset.parent_id))

        self.edtDatasetName.setText(dataset.dataset_name)
        self.edtDatasetDesc.setText(dataset.dataset_desc)
        if dataset.dimension == 2:
            self.rbtn2D.setChecked(True)
        elif dataset.dimension == 3:
            self.rbtn3D.setChecked(True)
        #print(dataset.dimension,self.dataset.objects)
        if len(self.dataset.objects) > 0:
            self.rbtn2D.setEnabled(False)
            self.rbtn3D.setEnabled(False)
        self.edtWireframe.setText(dataset.wireframe)
        self.edtBaseline.setText(dataset.baseline)
        self.edtPolygons.setText(dataset.polygons)
        self.edtPropertyNameList.setText(dataset.propertyname_list)
    
    def set_parent_dataset(self, parent_dataset):
        #print("parent:", parent_dataset_id, "dataset:", self.dataset)
        if parent_dataset is None:
            self.cbxParent.setCurrentIndex(-1)
        else:
            self.cbxParent.setCurrentIndex(self.cbxParent.findData(parent_dataset.id))
            if parent_dataset.dimension == 2:
                self.rbtn2D.setChecked(True)
            elif parent_dataset.dimension == 3:
                self.rbtn3D.setChecked(True)
            #self.rbtn2D.setEnabled(False)
            #self.rbtn3D.setEnabled(False)

    def Okay(self):
        if self.dataset is None:
            self.dataset = MdDataset()
        self.dataset.parent_id = self.cbxParent.currentData()
        self.dataset.dataset_name = self.edtDatasetName.text()
        self.dataset.dataset_desc = self.edtDatasetDesc.text()
        if self.rbtn2D.isChecked():
            self.dataset.dimension = 2
        elif self.rbtn3D.isChecked():
            self.dataset.dimension = 3
        self.dataset.wireframe = self.edtWireframe.toPlainText()
        self.dataset.baseline = self.edtBaseline.text()
        self.dataset.polygons = self.edtPolygons.toPlainText()
        self.dataset.propertyname_list = self.edtPropertyNameList.toPlainText()

        #self.data
        #print(self.dataset.dataset_desc, self.dataset.dataset_name)
        self.dataset.save()
        self.accept()

    def Delete(self):
        ret = QMessageBox.question(self, "", "Are you sure to delete this dataset?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        print("ret:", ret)
        if ret == QMessageBox.Yes:
            self.dataset.delete_instance()
            self.parent.selected_dataset = None
            #self.dataset.delete_dataset()
        #self.delete_dataset()
        self.accept()

    def Cancel(self):
        self.reject()

MODE_NONE = 0
MODE_PAN = 12
MODE_EDIT_LANDMARK = 1
MODE_EDIT_WIREFRAME = 2
import math

class dLabel(QLabel):
    #clicked = pyqtSignal()
    def __init__(self, widget):
        super(dLabel, self).__init__(widget)
        self.setAcceptDrops(True)
        self.orig_pixmap = None
        self.curr_pixmap = None
        self.scale = 1.0
        self.fullpath = None
        self.temp_pan_x = 0
        self.temp_pan_y = 0
        self.mouse_down_x = 0
        self.mouse_down_y = 0
        self.pan_x = 0
        self.pan_y = 0
        self.setMouseTracking(True)
        self.pan_mode = MODE_NONE
        self.set_mode(MODE_EDIT_LANDMARK)
        #self.edit_mode = MODE_ADD_LANDMARK
        self.first_resize = True
        self.curr_mouse_x = 0
        self.curr_mouse_y = 0
        self.image_canvas_ratio = 1.0
        self.setMinimumSize(640,480)
        self.show_index = True
        self.show_wireframe = False
        self.show_baseline = False
        #self.repaint()

#function _2canx( coord ) { return Math.round(( coord / gImageCanvasRatio ) * gScale) + gPanX + gTempPanX; }
#function _2cany( coord ) { return Math.round(( coord / gImageCanvasRatio ) * gScale) + gPanY + gTempPanY; }
    def _2canx(self, coord):
        return round((coord / self.image_canvas_ratio) * self.scale) + self.pan_x + self.temp_pan_x

    def _2cany(self, coord):
        return round((coord / self.image_canvas_ratio) * self.scale) + self.pan_y + self.temp_pan_y

    def _2imgx(self, coord):
        return round(((coord - self.pan_x) / self.scale) * self.image_canvas_ratio)

    def _2imgy(self, coord):
        return round(((coord - self.pan_y) / self.scale) * self.image_canvas_ratio)
    
    def set_mode(self, mode):
        self.edit_mode = mode  
        if self.edit_mode == MODE_EDIT_LANDMARK:
            self.setCursor(Qt.CrossCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def mouseMoveEvent(self, event):
        me = QMouseEvent(event)
        self.curr_mouse_x = me.x()
        self.curr_mouse_y = me.y()
        #print("mouse move event", me, me.pos(), self.curr_mouse_x, self.curr_mouse_y, self._2imgx(self.curr_mouse_x), self._2imgy(self.curr_mouse_y))
        if self.pan_mode == MODE_PAN:
            self.temp_pan_x = self.curr_mouse_x - self.mouse_down_x
            self.temp_pan_y = self.curr_mouse_y - self.mouse_down_y
            #print("pan", self.pan_x, self.pan_y, self.temp_pan_x, self.temp_pan_y)
            #self.downX = me.x()
            #self.downY = me.y()
        self.repaint()
        QLabel.mouseMoveEvent(self, event)

    def mousePressEvent(self, event):
        if self.orig_pixmap is None:
            return
        #self.clicked.emit()
        me = QMouseEvent(event)
        #print("event and pos", event, me.pos())
        if me.button() == Qt.LeftButton:

            #print("left button clicked", me.pos())
            if self.edit_mode == MODE_EDIT_LANDMARK:
                #print("add landmark")
                #print(self.object_dialog)
                img_x = self._2imgx(self.curr_mouse_x)
                img_y = self._2imgy(self.curr_mouse_y)
                if img_x < 0 or img_x > self.orig_pixmap.width() or img_y < 0 or img_y > self.orig_pixmap.height():
                    return
                self.object_dialog.add_landmark(str(img_x), str(img_y))
        elif me.button() == Qt.RightButton:
            self.pan_mode = MODE_PAN
            self.mouse_down_x = me.x()
            self.mouse_down_y = me.y()
            #print("right button clicked")
        elif me.button() == Qt.MidButton:
            print("middle button clicked")

        
        QLabel.mousePressEvent(self, event)

    def mouseReleaseEvent(self, ev: QMouseEvent) -> None:
        me = QMouseEvent(ev)
        #print("mouse release event", me, me.pos())
        if self.pan_mode == MODE_PAN:
            self.pan_mode = MODE_NONE
            self.pan_x += self.temp_pan_x
            self.pan_y += self.temp_pan_y
            self.temp_pan_x = 0
            self.temp_pan_y = 0
            self.repaint()
            #print("right button released")

        return super().mouseReleaseEvent(ev)    

    def wheelEvent(self, event):
        if self.orig_pixmap is None:
            return
        we = QWheelEvent(event)
        scale_delta = 0
        #print(we.angleDelta())
        if we.angleDelta().y() > 0:
            scale_delta = 0.1
        else:
            scale_delta = -0.1
        if self.scale <= 0.8 and scale_delta < 0:
            return
        if self.scale > 1:
            scale_delta *= math.floor(self.scale)
        
        prev_scale = self.scale
        self.scale += scale_delta
        self.scale = round(self.scale * 10) / 10
        scale_proportion = self.scale / prev_scale
        self.curr_pixmap = self.orig_pixmap.scaled(int(self.orig_pixmap.width() * self.scale / self.image_canvas_ratio), int(self.orig_pixmap.height() * self.scale / self.image_canvas_ratio))

        self.pan_x = int( we.pos().x() - (we.pos().x() - self.pan_x) * scale_proportion )
        self.pan_y = int( we.pos().y() - (we.pos().y() - self.pan_y) * scale_proportion )

        self.repaint()

        #print("wheel event", we, we.angleDelta())
        QLabel.wheelEvent(self, event)

    def set_image(self,file_path):
        self.fullpath = file_path
        self.curr_pixmap = self.orig_pixmap = QPixmap(file_path)
        self.setPixmap(self.curr_pixmap)

        #self.setScaledContents(True)
        #print( self.curr_pixmap.width(), self.curr_pixmap.height(), self.orig_pixmap.width(), self.orig_pixmap.height())

    def dragEnterEvent(self, event):
        file_name = event.mimeData().text()
        if file_name.split('.')[-1].lower() in ['png', 'jpg', 'jpeg','bmp','gif','tif','tiff']:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        file_path = event.mimeData().text()
        file_path = re.sub('file:///', '', file_path)
        #print(file_path)
        #self.setScaledContents(True)
        self.set_image(file_path)
        # resize self
        self.calculate_resize()

        #self.resize(self.width(), self.height())

    def paintEvent(self, event):
        #self.pixmap
        #return super().paintEvent(event)
        painter = QPainter(self)
        painter.fillRect(self.rect(), QBrush(QColor(100,100,100)))

        if self.orig_pixmap is None:
            return
        # fill background with dark gray
        
        #height = self.progress * self.height()
        #if self.orig_pixmap is not None:
            #painter.drawPixmap(self.rect(), self.orig_pixmap)
        if self.curr_pixmap is not None:                
            #self.curr_pixmap = self.orig_pixmap.scaled(int(self.orig_width/self.image_canvas_ratio),int(self.orig_width/self.image_canvas_ratio), Qt.KeepAspectRatio)            
            painter.drawPixmap(self.pan_x+self.temp_pan_x, self.pan_y+self.temp_pan_y,self.curr_pixmap)

        # if edit_mode = MODE_ADD_LANDMARK draw a circle at the mouse position
        #painter.setBrush(QBrush(Qt.red))
        radius = 3
        painter.setPen(QPen(Qt.red, 2))
        if self.edit_mode == MODE_EDIT_LANDMARK:
            img_x = self._2imgx(self.curr_mouse_x)
            img_y = self._2imgy(self.curr_mouse_y)
            if img_x < 0 or img_x > self.orig_pixmap.width() or img_y < 0 or img_y > self.orig_pixmap.height():
                pass
            else:
                painter.drawEllipse(self.curr_mouse_x-radius, self.curr_mouse_y-radius, radius*2, radius*2)

        for idx, landmark in enumerate(self.object_dialog.landmark_list):
            if landmark[0] == "":
                continue  
            painter.drawEllipse(self._2canx(int(landmark[0]))-5, self._2cany(int(landmark[1]))-5, 10, 10)
            painter.drawText(self._2canx(int(landmark[0]))+10, self._2cany(int(landmark[1]))+10, str(idx+1))

        #r = QRect(0, self.height() - 20, self.width(), 20)
        #painter.fillRect(r, QBrush(Qt.blue))
        #pen = QPen(QColor("red"), 10)
        #painter.setPen(pen)
        #painter.drawRect(self.rect())
    def calculate_resize(self):
        self.orig_width = self.orig_pixmap.width()
        self.orig_height = self.orig_pixmap.height()
        image_wh_ratio = self.orig_width / self.orig_height
        label_wh_ratio = self.width() / self.height()
        if image_wh_ratio > label_wh_ratio:
            self.image_canvas_ratio = self.orig_width / self.width()
        else:
            self.image_canvas_ratio = self.orig_height / self.height()
        self.curr_pixmap = self.orig_pixmap.scaled(int(self.orig_width*self.scale/self.image_canvas_ratio),int(self.orig_width*self.scale/self.image_canvas_ratio), Qt.KeepAspectRatio)

    def resizeEvent(self, event):
        if self.orig_pixmap is not None:
            self.calculate_resize()
            #print("image_wh_ratio", image_wh_ratio, "label_wh_ratio", label_wh_ratio, "image_canvas_ratio", self.image_canvas_ratio)
            self.first_resize = False
        #print("resize",self.size())
        # print size
        #print(event.size())
        #print(self.size())
        if self.curr_pixmap is not None:                
            #self.curr_pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatio)
            #print( self.curr_pixmap.width(), self.curr_pixmap.height(), self.orig_pixmap.width(), self.orig_pixmap.height())
            pass
        QLabel.resizeEvent(self, event)

class PicButton(QAbstractButton):
    def __init__(self, pixmap, pixmap_hover, pixmap_pressed, parent=None):
        super(PicButton, self).__init__(parent)
        self.pixmap = pixmap
        self.pixmap_hover = pixmap_hover
        self.pixmap_pressed = pixmap_pressed

        self.pressed.connect(self.update)
        self.released.connect(self.update)

    def paintEvent(self, event):
        pix = self.pixmap_hover if self.underMouse() else self.pixmap
        if self.isDown():
            pix = self.pixmap_pressed

        painter = QPainter(self)
        painter.drawPixmap(self.rect(), pix)

    def enterEvent(self, event):
        self.update()

    def leaveEvent(self, event):
        self.update()

    def sizeHint(self):
        return QSize(200, 200)

class ObjectDialog(QDialog):
    # NewDatasetDialog shows new dataset dialog.
    def __init__(self,parent):
        super().__init__()
        self.setWindowTitle("Object")
        self.parent = parent
        #print(self.parent.pos())
        self.setGeometry(QRect(100, 100, 1024, 600))
        self.move(self.parent.pos()+QPoint(100,100))

        self.hsplitter = QSplitter(Qt.Horizontal)
        self.vsplitter = QSplitter(Qt.Vertical)

        #self.vsplitter.addWidget(self.tableView)
        #self.vsplitter.addWidget(self.tableWidget)

        #self.hsplitter.addWidget(self.treeView)
        #self.hsplitter.addWidget(self.vsplitter)

        self.inputLayout = QHBoxLayout()
        self.inputCoords = QWidget()
        self.inputCoords.setLayout(self.inputLayout)
        self.inputX = QLineEdit()
        self.inputY = QLineEdit()
        self.inputZ = QLineEdit()

        self.inputLayout.addWidget(self.inputX)
        self.inputLayout.addWidget(self.inputY)
        self.inputLayout.addWidget(self.inputZ)
        self.inputLayout.setContentsMargins(0,0,0,0)
        self.inputLayout.setSpacing(0)
        self.btnAddInput = QPushButton()
        self.btnAddInput.setText("Add")
        self.inputLayout.addWidget(self.btnAddInput)
        self.inputX.returnPressed.connect(self.input_coords_process)
        self.inputY.returnPressed.connect(self.input_coords_process)
        self.inputZ.returnPressed.connect(self.input_coords_process)
        self.inputX.textChanged[str].connect(self.x_changed)
        self.btnAddInput.clicked.connect(self.input_coords_process)

        self.edtObjectName = QLineEdit()
        self.edtObjectDesc = QTextEdit()
        self.edtObjectDesc.setMaximumHeight(100)
        self.edtLandmarkStr = QTableWidget()
        self.lblDataset = QLabel()

        self.main_layout = QVBoxLayout()
        self.sub_layout = QHBoxLayout()
        self.setLayout(self.main_layout)

        self.image_label = dLabel(self)
        self.image_label.object_dialog = self
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        #self.image_label.clicked.connect(self.on_image_clicked)

        self.pixmap = QPixmap(1024,768)
        self.image_label.setPixmap(self.pixmap)
        #self.image_label.setScaledContents(True)
        self.image_layout = QHBoxLayout()
        self.image_layout.addWidget(self.image_label)

        self.form_layout = QFormLayout()
        self.form_layout.addRow("Dataset Name", self.lblDataset)
        self.form_layout.addRow("Object Name", self.edtObjectName)
        self.form_layout.addRow("Object Desc", self.edtObjectDesc)
        self.form_layout.addRow("Landmarks", self.edtLandmarkStr)
        self.form_layout.addRow("", self.inputCoords)

        self.btnGroup = QButtonGroup() 
        self.btnLandmark = PicButton(QPixmap("icon/landmark.png"), QPixmap("icon/landmark_hover.png"), QPixmap("icon/landmark_down.png"))
        self.btnWireframe = PicButton(QPixmap("icon/wireframe.png"), QPixmap("icon/wireframe_hover.png"), QPixmap("icon/wireframe_down.png"))
        self.btnGroup.addButton(self.btnLandmark, 0)
        self.btnGroup.addButton(self.btnLandmark, 0)
        self.btnLandmark.setCheckable(True)
        self.btnWireframe.setCheckable(True)
        self.btnLandmark.setChecked(True)
        self.btnWireframe.setChecked(False)
        self.btnLandmark.setAutoExclusive(True)
        self.btnWireframe.setAutoExclusive(True)
        self.btnLandmark.clicked.connect(self.landmark_clicked)
        self.btnWireframe.clicked.connect(self.wireframe_clicked)

        self.btnLandmark.setFixedSize(32,32)
        self.btnWireframe.setFixedSize(32,32)

        self.cbxShowIndex = QCheckBox()
        self.cbxShowIndex.setText("Show Index")
        self.cbxShowIndex.setChecked(True)

        #self.btnLandmark = QPushButton()
        #self.btnLandmark2 = QPushButton()
        #self.btnLandmark.setIcon(QIcon("icon/landmark_24.png"))
        #self.btnLandmark.setText("1")
        #self.btnLandmark2.setText("2")
        self.btn_layout2 = QGridLayout()
        self.btn_layout2.addWidget(self.btnLandmark,0,0)
        self.btn_layout2.addWidget(self.btnWireframe,0,1)
        #self.btn_layout2.addWidget(self.cbxShowIndex,1,0,1,2)

        #self.sub_layout.addLayout(self.form_layout)
        #self.sub_layout.addLayout(self.image_layout)
        self.left_widget = QWidget()
        self.left_widget.setLayout(self.form_layout)
        self.center_widget = QWidget()
        self.center_widget.setLayout(self.image_layout)
        self.right_top_widget = QWidget()
        self.right_top_widget.setLayout(self.btn_layout2)
        self.right_bottom_widget = QWidget()

        self.vsplitter.addWidget(self.right_top_widget)
        self.vsplitter.addWidget(self.right_bottom_widget)
        self.vsplitter.setSizes([50,400])
        self.vsplitter.setStretchFactor(0, 0)
        self.vsplitter.setStretchFactor(1, 1)

        self.hsplitter.addWidget(self.left_widget)
        self.hsplitter.addWidget(self.image_label)
        self.hsplitter.addWidget(self.vsplitter)
        #self.hsplitter.addWidget(self.right_widget)
        self.hsplitter.setSizes([200,800,100])
        self.hsplitter.setStretchFactor(0, 0)
        self.hsplitter.setStretchFactor(1, 1)
        self.hsplitter.setStretchFactor(2, 0)

        self.btnOkay = QPushButton()
        self.btnOkay.setText("Save")
        self.btnOkay.clicked.connect(self.Okay)
        self.btnDelete = QPushButton()
        self.btnDelete.setText("Delete")
        self.btnDelete.clicked.connect(self.Delete)
        self.btnCancel = QPushButton()
        self.btnCancel.setText("Cancel")
        self.btnCancel.clicked.connect(self.Cancel)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btnOkay)
        btn_layout.addWidget(self.btnDelete)
        btn_layout.addWidget(self.btnCancel)

        #self.main_layout.addLayout(self.sub_layout)
        self.main_layout.addWidget(self.hsplitter)
        self.main_layout.addLayout(btn_layout)

        self.dataset = None
        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.landmark_list = []

        #self.edtDataFolder.setText(str(self.data_folder.resolve()))
        #self.edtServerAddress.setText(self.server_address)
        #self.edtServerPort.setText(self.server_port)

    '''
    @pyqtSlot()
    def on_image_clicked(self,event):
        print("clicked")
        print(event.pos())
        #pass
    '''

    def landmark_clicked(self):
        #self.edit_mode = MODE_ADD_LANDMARK
        self.image_label.set_mode(MODE_EDIT_LANDMARK)
        self.image_label.update()
        self.btnLandmark.setDown(True)
        self.btnLandmark.setChecked(True)

    def wireframe_clicked(self):
        #self.edit_mode = MODE_ADD_LANDMARK
        self.image_label.set_mode(MODE_EDIT_WIREFRAME)
        self.image_label.update()
        self.btnWireframe.setDown(True)
        self.btnWireframe.setChecked(True)

    def set_dataset(self, dataset):
        self.dataset = dataset
        self.lblDataset.setText(dataset.dataset_name)

        header = self.edtLandmarkStr.horizontalHeader()    
        if self.dataset.dimension == 2:
            self.edtLandmarkStr.setColumnCount(2)
            self.edtLandmarkStr.setHorizontalHeaderLabels(["X","Y"])
            #self.edtLandmarkStr.setColumnWidth(0, 80)
            #self.edtLandmarkStr.setColumnWidth(1, 80)
            header.setSectionResizeMode(0, QHeaderView.Stretch)
            header.setSectionResizeMode(1, QHeaderView.Stretch)
            self.inputZ.hide()
            input_width = 80
        elif self.dataset.dimension == 3:
            self.edtLandmarkStr.setColumnCount(3)
            self.edtLandmarkStr.setHorizontalHeaderLabels(["X","Y","Z"])
            header.setSectionResizeMode(0, QHeaderView.Stretch)
            header.setSectionResizeMode(1, QHeaderView.Stretch)
            header.setSectionResizeMode(2, QHeaderView.Stretch)
            self.inputZ.show()
            input_width = 60
            
        #self.inputX.setFixedWidth(input_width)
        #self.inputY.setFixedWidth(input_width)
        #self.inputZ.setFixedWidth(input_width)
        #self.btnAddInput.setFixedWidth(input_width)
        

    @pyqtSlot(str)
    def x_changed(self, text):
        # if text is multiline and tab separated, add to table
        #print("x_changed called with", text)
        if "\n" in text:
            lines = text.split("\n")
            for line in lines:
                #print(line)
                if "\t" in line:
                    coords = line.split("\t")
                    #add landmarks using add_landmark method
                    if self.dataset.dimension == 2 and len(coords) == 2:
                        self.add_landmark(coords[0], coords[1])
                    elif self.dataset.dimension == 3 and len(coords) == 3:
                        self.add_landmark(coords[0], coords[1], coords[2])
            self.inputX.setText("")
            self.inputY.setText("")
            self.inputZ.setText("")

    def add_landmark(self, x, y, z=None):
        #print("adding landmark", x, y, z)
        # show landmark count in table
        #print(self.edtLandmarkStr.rowCount())
        if self.dataset.dimension == 2:
            self.edtLandmarkStr.setRowCount(self.edtLandmarkStr.rowCount()+1)
            self.edtLandmarkStr.setItem(self.edtLandmarkStr.rowCount()-1, 0, QTableWidgetItem(x))
            self.edtLandmarkStr.setItem(self.edtLandmarkStr.rowCount()-1, 1, QTableWidgetItem(y))
            self.landmark_list.append([x,y])
        elif self.dataset.dimension == 3:
            self.edtLandmarkStr.setRowCount(self.edtLandmarkStr.rowCount()+1)
            self.edtLandmarkStr.setItem(self.edtLandmarkStr.rowCount()-1, 0, QTableWidgetItem(x))
            self.edtLandmarkStr.setItem(self.edtLandmarkStr.rowCount()-1, 1, QTableWidgetItem(y))
            self.edtLandmarkStr.setItem(self.edtLandmarkStr.rowCount()-1, 2, QTableWidgetItem(z))
            self.landmark_list.append([x,y,z])
        #print(self.edtLandmarkStr.rowCount())


    def input_coords_process(self):
        x_str = self.inputX.text()
        y_str = self.inputY.text()
        z_str = self.inputZ.text()
        if self.dataset.dimension == 2:
            if x_str == "" or y_str == "":
                return
            # add landmark to table using add_landmark method
            self.add_landmark(x_str, y_str)

        elif self.dataset.dimension == 3:
            if x_str == "" or y_str == "" or z_str == "":
                return
            self.add_landmark(x_str, y_str, z_str)
        self.inputX.setText("")
        self.inputY.setText("")
        self.inputZ.setText("")
        self.inputX.setFocus()

    def set_object(self, object):
        #print("set_object", self.image_label.size())
        self.object = object
        self.edtObjectName.setText(object.object_name)
        self.edtObjectDesc.setText(object.object_desc)
        #self.edtLandmarkStr.setText(object.landmark_str)
        self.landmark_list = []
        self.show_landmarks(object.landmark_str)
        if object.image is not None and len(object.image) > 0:
            img = object.image[0]
            self.image_label.set_image(img.original_path)
        #self.set_dataset(object.dataset)

    def save_object(self):
        if self.object is None:
            self.object = MdObject()
        self.object.dataset_id = self.dataset.id
        self.object.object_name = self.edtObjectName.text()
        self.object.object_desc = self.edtObjectDesc.toPlainText()
        #self.object.landmark_str = self.edtLandmarkStr.text()
        self.object.landmark_str = self.make_landmark_str()
        self.object.save()
        if self.image_label.fullpath is not None:
            md_image = MdImage()
            md_image.object_id = self.object.id
            md_image.load_file_info(self.image_label.fullpath)
            md_image.save()

    def make_landmark_str(self):
        # from table, make landmark_str
        landmark_str = ""
        for row in range(self.edtLandmarkStr.rowCount()):
            for col in range(self.edtLandmarkStr.columnCount()):
                landmark_str += self.edtLandmarkStr.item(row, col).text()
                if col < self.edtLandmarkStr.columnCount()-1:
                    landmark_str += "\t"
            if row < self.edtLandmarkStr.rowCount()-1:
                landmark_str += "\n"
        return landmark_str

    def show_landmarks(self,landmark_str):
        # from landmark_str, show landmarks
        #landmark_str = self.object.landmark_str
        #print(landmark_str)
        if landmark_str == "":
            return
        lines = landmark_str.split("\n")
        landmark_count = 0

        for line in lines:
            coords = line.split("\t")
            if len(coords) >= 2 and self.dataset.dimension == 2:
                self.add_landmark(coords[0], coords[1])
                landmark_count += 1
            elif len(coords) == 3 and self.dataset.dimension == 3:
                self.add_landmark(coords[0], coords[1], coords[2])
                landmark_count += 1
        

    def Delete(self):
        ret = QMessageBox.question(self, "", "Are you sure to delete this object?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if ret == QMessageBox.Yes:
            self.object.delete_instance()
        #self.delete_dataset()
        self.accept()

    def Okay(self):
        self.save_object()
        self.accept()

    def Cancel(self):
        self.reject()

    def resizeEvent(self, event):
        #print("Window has been resized",self.image_label.width(), self.image_label.height())
        #self.pixmap.scaled(self.image_label.width(), self.image_label.height(), Qt.KeepAspectRatio)
        #self.edtObjectDesc.resize(self.edtObjectDesc.height(),300)
        #self.image_label.setPixmap(self.pixmap)
        QDialog.resizeEvent(self, event)

class PreferencesDialog(QDialog):
    '''
    PreferencesDialog shows preferences.

    Args:
        None

    Attributes:
        well..
    '''
    def __init__(self,parent):
        super().__init__()
        self.parent = parent
        self.setGeometry(QRect(0, 0, 400, 300))
        self.setWindowTitle("설정")
        #self.lbl_main_view.setMinimumSize(400, 300)

        self.lblServerAddress = QLabel()
        self.edtServerAddress = QLineEdit()
        self.edtServerPort = QLineEdit()
        self.lblDataFolder = QLabel()
        self.edtDataFolder = QLineEdit()

        self.edtServerPort.setFixedWidth(50)

        self.btnDataFolder = QPushButton()
        self.btnDataFolder.setText("선택")
        self.btnDataFolder.clicked.connect(self.select_folder)

        self.btnOkay = QPushButton()
        self.btnOkay.setText("확인")
        self.btnOkay.clicked.connect(self.Okay)

        self.btnCancel = QPushButton()
        self.btnCancel.setText("취소")
        self.btnCancel.clicked.connect(self.Cancel)


        self.layout = QVBoxLayout()
        self.layout1 = QHBoxLayout()
        self.layout1.addWidget(self.lblServerAddress)
        self.layout1.addWidget(self.edtServerAddress)
        self.layout1.addWidget(self.edtServerPort)
        self.layout3 = QHBoxLayout()
        self.layout3.addWidget(self.lblDataFolder)
        self.layout3.addWidget(self.edtDataFolder)
        self.layout3.addWidget(self.btnDataFolder)
        self.layout4 = QHBoxLayout()
        self.layout4.addWidget(self.btnOkay)
        self.layout4.addWidget(self.btnCancel)
        self.layout.addLayout(self.layout1)
        #self.layout.addLayout(self.layout2)
        self.layout.addLayout(self.layout3)
        self.layout.addLayout(self.layout4)
        self.setLayout(self.layout)
        self.server_address = ''
        self.server_port = ''
        self.data_folder = ''
        #print("pref dlg data_folder:", self.data_folder)
        self.read_settings()
        #print("pref dlg data_folder:", self.data_folder)
        self.lblServerAddress.setText("서버 주소")
        #self.lblServerPort.setText("Server Port")
        self.lblDataFolder.setText("사진 위치")

        #self.edtDataFolder.setText(str(self.data_folder.resolve()))
        self.edtServerAddress.setText(self.server_address)
        self.edtServerPort.setText(self.server_port)

    def write_settings(self):
        self.parent.server_address = self.edtServerAddress.text()
        self.parent.server_port = self.edtServerPort.text()
        self.parent.data_folder = Path(self.edtDataFolder.text())
        #print( self.parent.server_address,self.parent.server_port, self.parent.data_folder)

    def read_settings(self):
        self.server_address = self.parent.server_address
        self.server_port = self.parent.server_port
        self.data_folder = self.parent.data_folder.resolve()
        #print("pref dlg data folder:", self.data_folder)
        #print("pref dlg server address:", self.server_address)

    def Okay(self):
        self.write_settings()
        self.close()

    def Cancel(self):
        self.close()

    def select_folder(self):
        folder = str(QFileDialog.getExistingDirectory(self, "폴더 선택", str(self.data_folder)))
        if folder:
            self.data_folder = Path(folder).resolve()
            self.edtDataFolder.setText(folder)



form_class = uic.loadUiType("Modan2.ui")[0]
class ModanMainWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        #QApplication.setOverrideCursor(Qt.WaitCursor)
        self.setupUi(self)
        self.setGeometry(QRect(100, 100, 1200, 800))
        self.initUI()
        self.setWindowTitle(PROGRAM_NAME)
        #self.read_settings()
        self.check_db()
        self.reset_views()
        self.load_dataset()
        #QApplication.restoreOverrideCursor()
        self.selected_dataset = None
        self.selected_object = None

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
        #self.write_settings()
        event.accept()

    def on_actionPreferences_triggered(self):
        dlg = PreferencesDialog(self)
        dlg.exec_()
        self.server_address = dlg.server_address
        self.server_port = dlg.server_port
        self.data_folder = dlg.data_folder
        #print("main window data folder:", self.data_folder)
        #print("main window server address:", self.server_address)
    
    def on_actionExit_triggered(self):
        self.close()

    def on_actionAbout_triggered(self):
        QMessageBox.about(self, "About", "Modan2")

    def initUI(self):
        # add tableView and tableWidget to vertical layout
        #widget = QWidget()
        hsplitter = QSplitter(Qt.Horizontal)
        vsplitter = QSplitter(Qt.Vertical)

        vsplitter.addWidget(self.tableView)
        vsplitter.addWidget(self.tableWidget)

        hsplitter.addWidget(self.treeView)
        hsplitter.addWidget(vsplitter)
        hsplitter.setSizes([300, 800])

        self.setCentralWidget(hsplitter)

        self.treeView.doubleClicked.connect(self.on_treeView_doubleClicked)
        self.treeView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableView.doubleClicked.connect(self.on_tableView_doubleClicked)
        self.tableView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        self.treeView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeView.customContextMenuRequested.connect(self.open_menu)

        #self.treeView.

    def open_menu(self, position):
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
        print("import dataset")
        # open import dataset dialog
        self.dlg = ImportDatasetDialog(self)
        self.dlg.setModal(True)
        self.dlg.setWindowModality(Qt.ApplicationModal)
        self.dlg.exec_()
        self.load_dataset()        

    @pyqtSlot()
    def on_action_export_dataset_triggered(self):
        print("export dataset")

    @pyqtSlot()
    def on_action_new_object_triggered(self):
        # open new object dialog
        #return
        if not self.selected_dataset:
            return
        self.dlg = ObjectDialog(self)
        self.dlg.setModal(True)
        self.dlg.object = None
        self.dlg.set_dataset(self.selected_dataset)
        #self.dlg.setWindowModality(Qt.ApplicationModal)
        #print("new dataset dialog")
        self.dlg.exec_()
        self.load_object()
        #print("new dataset dialog shown")
        # create new dataset

    @pyqtSlot()
    def on_action_new_dataset_triggered(self):
        # open new dataset dialog
        #return
        self.dlg = DatasetDialog(self)
        self.dlg.setModal(True)
        if self.selected_dataset:
            print("selected exists")
            self.dlg.set_parent_dataset( self.selected_dataset )
        else:
            print("selected not exists")
            self.dlg.set_parent_dataset( None )

        #self.dlg.setWindowModality(Qt.ApplicationModal)
        #print("new dataset dialog")
        ret = self.dlg.exec_()
        print("dataset edit result:", ret)
        self.load_dataset()
        self.reset_tableView()
        #print("new dataset dialog shown")
        # create new dataset

    @pyqtSlot()
    def on_treeView_doubleClicked(self):
        #print("treeView double clicked")
        self.dlg = DatasetDialog(self)
        self.dlg.setModal(True)
        self.dlg.set_dataset( self.selected_dataset )
        #self.dlg.setWindowModality(Qt.ApplicationModal)
        #print("new dataset dialog")
        ret = self.dlg.exec_()
        if ret == 0:
            return
        elif ret == 1:
            if self.selected_dataset is None: #deleted
                self.load_dataset()
                self.reset_tableView()
            else:
                dataset = self.selected_dataset
                self.load_dataset()
                self.reset_tableView()
                self.select_dataset(dataset)

        print("dataset edit result:", ret, self.selected_dataset)
        #self.load_dataset()
        #self.reset_tableView()
    
    def select_dataset(self,dataset,node=None):
        #print("select dataset:", dataset)
        if dataset is None:
            return
        if node is None:
            node = self.dataset_model.invisibleRootItem()
        #print("node:", node)
        for i in range(node.rowCount()):
            item = node.child(i,1)
            #print("item:", item, item.data(),dataset)

            if item.data() == dataset:
                self.treeView.setCurrentIndex(item.index())
                break
            self.select_dataset(dataset,node.child(i,0))


    @pyqtSlot()
    def on_tableView_doubleClicked(self):
        #print("treeView double clicked")
        self.dlg = ObjectDialog(self)
        self.dlg.setModal(True)
        self.dlg.set_dataset(self.selected_dataset)
        self.dlg.set_object( self.selected_object )
        #self.dlg.setWindowModality(Qt.ApplicationModal)
        #print("new dataset dialog")
        self.dlg.exec_()
        self.load_object()

    def reset_treeView(self):
        self.dataset_model = QStandardItemModel()
        self.treeView.setModel(self.dataset_model)
        self.treeView.setHeaderHidden(True)
        self.dataset_selection_model = self.treeView.selectionModel()
        self.dataset_selection_model.selectionChanged.connect(self.on_dataset_selection_changed)
        #self.treeView
        header = self.treeView.header()
        #header.setStretchLastSection(False)
        self.treeView.setSelectionBehavior(QTreeView.SelectRows)
        #header.setSectionResizeMode(0, QHeaderView.Stretch)
        #header.setSectionResizeMode(1, QHeaderView.Fixed)

        #self.treeView.header().setSectionResizeMode(0, QHeaderView.Stretch)
        #self.treeView.header().setSectionResizeMode(1, QHeaderView.Fixed)
        #self.treeView.header().setSectionResizeMode(2, QHeaderView.Fixed)

        self.treeView.setColumnWidth(1, 50)
        #self.treeView.setColumnWidth(2, 50)

    def reset_tableView(self):
        self.object_model = QStandardItemModel()
        self.object_model.setColumnCount(4)
        self.object_model.setHorizontalHeaderLabels(["ID", "Name", "Count", "CSize"])
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.object_model)
        self.tableView.setModel(self.proxy_model)
        self.tableView.setColumnWidth(0, 50)
        self.tableView.setColumnWidth(1, 200)
        self.tableView.setColumnWidth(2, 200)
        self.tableView.setColumnWidth(3, 200)
        self.tableView.verticalHeader().setDefaultSectionSize(20)
        self.tableView.verticalHeader().setVisible(False)
        self.tableView.setSelectionBehavior(QTableView.SelectRows)
        self.object_selection_model = self.tableView.selectionModel()
        self.object_selection_model.selectionChanged.connect(self.on_object_selection_changed)

    def reset_views(self):
        self.reset_treeView()
        self.reset_tableView()
    
    def load_dataset(self):
        self.dataset_model.clear()
        self.selected_dataset = None
        all_record = MdDataset.filter(parent=None)
        for rec in all_record:
            item1 = QStandardItem(rec.dataset_name + " (" + str(rec.objects.count()) + ")")
            if rec.dimension == 2:
                item1.setIcon(QIcon("icon/icons8-xlarge-icons-50.png"))
            else:
                item1.setIcon(QIcon("icon/icons8-3d-50.png"))
            item2 = QStandardItem(str(rec.id))
            item2.setData(rec)
            #item3 = QStandardItem(str(rec.dimension))
            #print("dataset id:",item2.text())
            #item2 = QStandardItem(rec.objects.count())
            #sub_item2 = QStandardItem(str(Path(rec.path).as_posix()))
            #sub_item2 = QStandardItem(rec.)
            #sub_item.setData(rec)
            
            self.dataset_model.appendRow([item1,item2])#,item2,item3] )
            if rec.children.count() > 0:
                self.load_subdataset(item1,item2.data())
        self.treeView.expandAll()
        self.treeView.hideColumn(1)
        #self.treeView.hideColumn(2)

            #item.appendRow([sub_item1,sub_item2])
    def load_subdataset(self, parent_item, dataset):
        all_record = MdDataset.filter(parent=dataset)
        for rec in all_record:
            item1 = QStandardItem(rec.dataset_name + " (" + str(rec.objects.count()) + ")")
            if rec.dimension == 2:
                item1.setIcon(QIcon("icon/icons8-xlarge-icons-50.png")) #  https://icons8.com
            else:
                item1.setIcon(QIcon("icon/icons8-3d-50.png"))
            #item1 = QStandardItem(rec.dataset_name)
            item2 = QStandardItem(str(rec.id))
            item2.setData(rec)
            #item3 = QStandardItem(str(rec.dimension))
            #print("dataset id:",item2.text())
            #sub_item2 = QStandardItem(str(Path(rec.path).as_posix()))
            #sub_item2 = QStandardItem(rec.)
            #sub_item.setData(rec)
            parent_item.appendRow([item1,item2])#,item3] )
            if rec.children.count() > 0:
                self.load_subdataset(item1,item2.data())

            #item.appendRow([sub_item1,sub_item2]

    def on_dataset_selection_changed(self, selected, deselected):
        indexes = selected.indexes()
        #print(indexes)
        if indexes:
            self.object_model.clear()
            self.reset_tableView()        
            item1 =self.dataset_model.itemFromIndex(indexes[0])
            item2 =self.dataset_model.itemFromIndex(indexes[1])
            ds = item2.data()
            self.selected_dataset = ds
            self.load_object()

    def load_object(self):
        self.object_model.clear()
        self.reset_tableView()
        if self.selected_dataset is None:
            return
        #objects = self.selected_dataset.objects
        for obj in self.selected_dataset.objects:
            item1 = QStandardItem(str(obj.id))
            item2 = QStandardItem(obj.object_name)
            item3 = QStandardItem(str(obj.count_landmarks()))
            item1.setData(obj)
            self.object_model.appendRow([item1,item2,item3] )


    def on_object_selection_changed(self, selected, deselected):
        selected_index_list = self.object_selection_model.selection().indexes()
        if len(selected_index_list) == 0:
            return
        #print("selected_index",selected_index_list)

        new_index_list = []
        model = selected_index_list[0].model()
        if hasattr(model, 'mapToSource'):
            for index in selected_index_list:
                new_index = model.mapToSource(index)
                new_index_list.append(new_index)
        #print("new_index_list",new_index_list)
        item_text_list = []
        for index in new_index_list:
            item = self.object_model.itemFromIndex(index)
            #print("item_text:",item.text())
            item_text_list.append(item)
        self.selected_object = item_text_list[0].data()
        #print(selected_object,selected_object.object_name)
        #filepath = item_text_list[1]
        #filename = item_text_list[0]
        #return filepath, filename



    def _on_object_selection_changed(self, selected, deselected):
        indexes = selected.indexes()
        print(indexes)
        item1 = self.proxy_model.itemFromIndex(indexes[0])
        print(item1)

        indexes = self.object_selection_model.selection().indexes()
        print(indexes)
        item1 = self.proxy_model.itemFromIndex(indexes[0])
        print(item1)
        #item2 = self.dir_model.itemFromIndex(index_list[1])

if __name__ == "__main__":
    #QApplication : 프로그램을 실행시켜주는 클래스
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('Modan2.ico'))

    #WindowClass의 인스턴스 생성
    myWindow = ModanMainWindow()

    #프로그램 화면을 보여주는 코드
    myWindow.show()

    #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()
