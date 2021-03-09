# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main.ui'
#
# Created by: PyQt5 UI code generator 5.15.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1513, 939)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.image_list = SImageList(self.centralwidget)
        self.image_list.setGeometry(QtCore.QRect(1270, 500, 231, 381))
        self.image_list.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.image_list.setFrameShadow(QtWidgets.QFrame.Raised)
        self.image_list.setObjectName("image_list")
        self.model_list = SModelList(self.centralwidget)
        self.model_list.setGeometry(QtCore.QRect(10, 10, 381, 891))
        self.model_list.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.model_list.setFrameShadow(QtWidgets.QFrame.Raised)
        self.model_list.setObjectName("model_list")
        self.vtk_panel = SLabel3DAnnotation(self.centralwidget)
        self.vtk_panel.setGeometry(QtCore.QRect(390, 30, 871, 841))
        self.vtk_panel.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.vtk_panel.setFrameShadow(QtWidgets.QFrame.Raised)
        self.vtk_panel.setObjectName("vtk_panel")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1513, 26))
        self.menubar.setObjectName("menubar")
        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.action_Load_Scenes = QtWidgets.QAction(MainWindow)
        self.action_Load_Scenes.setObjectName("action_Load_Scenes")
        self.action_Save_Scenes = QtWidgets.QAction(MainWindow)
        self.action_Save_Scenes.setObjectName("action_Save_Scenes")
        self.menu.addAction(self.action_Load_Scenes)
        self.menu.addAction(self.action_Save_Scenes)
        self.menubar.addAction(self.menu.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.menu.setTitle(_translate("MainWindow", "文件"))
        self.action_Load_Scenes.setText(_translate("MainWindow", "&Load Scenes"))
        self.action_Load_Scenes.setShortcut(_translate("MainWindow", "Ctrl+O"))
        self.action_Save_Scenes.setText(_translate("MainWindow", "&Save Scenes"))
        self.action_Save_Scenes.setShortcut(_translate("MainWindow", "Ctrl+S"))
from simagelist import SImageList
from slabel3dannotation import SLabel3DAnnotation
from smodellist import SModelList
