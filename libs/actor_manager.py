import os
import sys
import vtk
import cv2
import json
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import PyQt5
from PyQt5 import QtCore, QtWidgets, QtGui
import typing
import math
from libs.utils.utils import *
from PyQt5.QtCore import pyqtSignal
from PyQt5.Qt import QObject
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from libs.smodellist import SModelList
from itertools import product
import itertools
from libs.lsystem_config import SystemConfig
from PIL import Image


class Actor:
    def __init__(self, render_window, interactor, model_path, model_class, model_name, layer_num, actor_id=0):
        self.renderer_window = render_window
        self.interactor = interactor
        self.renderer = None
        self.actor = None
        self.box_widget = None
        self.model_path = model_path
        self.model_name = model_name
        self.createRenderer(layer_num)
        self.loadModel(model_path, model_name)
        self.type_class = model_class
        self.size = []  # [w, l, h]
        self.actor_id = actor_id

    def readObj(self, model_path):
        reader = vtk.vtkOBJReader()
        reader.SetFileName(model_path)
        reader.Update()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(reader.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        return actor

    def importObj(self, model_path):
        self.model_folder, self.obj_name = os.path.split(self.model_path)
        self.obj_name = self.obj_name[:-4]
        self.mtl_path = self.model_folder + "/" + self.obj_name + ".mtl"
        importer = vtk.vtkOBJImporter()
        importer.SetFileName(self.model_path)
        importer.SetFileNameMTL(self.mtl_path)
        importer.SetTexturePath(self.model_folder)

        importer.Read()
        importer.InitializeObjectBase()

        # get all actors and assembly
        actors = importer.GetRenderer().GetActors()
        actors.InitTraversal()
        assembly = vtk.vtkAssembly()
        for i in range(actors.GetNumberOfItems()):
            a = actors.GetNextActor()
            assembly.AddPart(a)

        return assembly

    def loadModel(self, model_path, model_name):
        self.model_path = model_path
        self.model_name = model_name
        self.actor = SModelList.get().getActor(model_path)
        if self.actor is None:
            self.actor = self.readObj(model_path)
        # self.actor = self.importObj(model_path)

        # # move the actor to (0, 0, 0)
        # min_x, _, min_y, _, min_z, _ = self.actor.GetBounds()
        # transform = vtk.vtkTransform()
        # transform.Translate(-min_x, -min_y, -min_z)
        # self.actor.SetUserTransform(transform)

        self.renderer.AddActor(self.actor)
        self.interactor.Render()

    def createRenderer(self, layer_num):
        self.renderer = vtk.vtkRenderer()
        self.renderer_window.SetNumberOfLayers(layer_num + 1)
        self.renderer.SetLayer(layer_num)
        self.renderer.SetBackground(0, 0, 0)
        self.renderer.InteractiveOff()
        self.renderer.SetBackgroundAlpha(0)
        self.renderer.SetActiveCamera(
            self.renderer_window.GetRenderers().GetFirstRenderer().GetActiveCamera()
        )
        self.renderer_window.AddRenderer(self.renderer)
        return self.renderer

    def setUserTransform(self, transform):
        # self.box_widget.SetTransform(transform)
        self.actor.SetUserTransform(transform)

    def setMatrix(self, matrix):
        if type(self) is Actor:
            actor = self.actor
        else:
            actor = self
        setActorMatrix(actor, matrix)

    @staticmethod
    def get8Corners(prop3D):
        return getActorRotatedBounds(prop3D)

    def getCameraMatrix(self):
        matrix = self.renderer.GetActiveCamera().GetModelViewTransformMatrix()
        return [matrix.GetElement(i, j) for i in range(4) for j in range(4)]

    def getBBox2D(self):
        bbox3d_points_world = getActorRotatedBounds(self.actor)

        bbox3d_min_x, bbox3d_min_y, bbox3d_max_x, bbox3d_max_y \
            = worldToViewBBox(self.renderer, bbox3d_points_world)

        image_ratio = self.interactor.parent().image_ratio
        w, h = self.interactor.parent().image_width, self.interactor.parent().image_height
        image_points_world = [[-0.5, 0.5 / image_ratio, 0], [0.5, -0.5 / image_ratio, 0]]
        image_min_x, image_min_y, image_max_x, image_max_y = worldToViewBBox(self.renderer, image_points_world)
        w_i = image_max_x - image_min_x
        h_i = image_max_y - image_min_y
        p = np.dot(np.array([
            [w / 2, 0, w / 2],
            [0, -h / 2, h / 2],
            [0, 0, 1]
        ]), np.array([
            [2 / w_i, 0, 0],
            [0, 2 / h_i, 0],
            [0, 0, 1]
        ]))
        l, t, _ = np.dot(p, np.array([bbox3d_min_x, bbox3d_max_y, 1]).T)
        r, b, _ = np.dot(p, np.array([bbox3d_max_x, bbox3d_min_y, 1]).T)

        # test the labeled images
        # img = cv2.imread(self.interactor.parent().image_path)
        # img = cv2.rectangle(img, (int(l), int(t)), (int(r), int(b)), [0, 0, 255], 3)
        # cv2.imshow("rect", img)
        # cv2.waitKey(0)

        return round(l, 2), round(t, 2), round(r, 2), round(b, 2)

    def getBBox3D(self):
        """
        Returns:
            (8,2) array of vertices for the 3d box in following order:
            1 -------- 0
           /|         /|
          2 -------- 3 .
          | |        | |
          . 5 -------- 4
          |/         |/
          6 -------- 7

        """
        renderer = self.renderer
        w, h = Image.open(self.interactor.parent().parent().parent().image_list.file_list[0]).size

        P_v2i = getMatrixW2I(renderer, w, h)
        pts_3d = getActorRotatedBounds(self.actor)

        p_v = np.array(worldToView(renderer, pts_3d))
        p_i = np.dot(P_v2i, cart2hom(p_v[:, :2]).T).T[:, :2]
        return [[int(p_i[i][0]), int(p_i[i][1])] for i in range(0, 8)]

    def getBBox3D_w(self):
        """
               Returns:
                   (8,2) array of vertices for the 3d box in following order:
                   1 -------- 0
                  /|         /|
                 2 -------- 3 .
                 | |        | |
                 . 5 -------- 4
                 |/         |/
                 6 -------- 7

               """
        renderer = self.renderer
        w, h = Image.open(self.interactor.parent().parent().parent().image_list.file_list[0]).size

        P_v2i = getMatrixW2I(renderer, w, h)
        pts_3d = getActorRotatedBounds(self.actor)
        return pts_3d.tolist()

    def toJson(self, scene_folder):
        R_c2o = get_R_obj2c(np.array(matrix2List(self.actor.GetMatrix()))).reshape(1, 9).tolist()[0]
        camera_fov = self.interactor.parent().parent().parent().camera_property.get("fov")
        T_c2o = get_T_obj2c(np.array(matrix2List(self.actor.GetMatrix())), camera_fov)
        T_c2o = np.array([-T_c2o[0], T_c2o[1], -T_c2o[2]]).reshape(1, 3).tolist()[0]
        return {
            "model_file": os.path.relpath(self.model_path, scene_folder),
            "matrix": matrix2List(self.actor.GetMatrix()),
            "actor_id": int(self.actor_id),
            "R_matrix_c2o": R_c2o,
            "T_matrix_c2o": T_c2o,
            "class": self.type_class,
            "class_name": self.model_name,
            "size": listRound(self.size),
            "2d_bbox": self.getBBox2D(),
            "3d_bbox": self.getBBox3D(),
            "3d_bbox_w": self.getBBox3D_w()
        }

    def toKITTI(self):
        # get bottom center point
        p = np.array([self.actor.GetPosition()])
        p = cart2hom(p)

        camera = self.renderer.GetActiveCamera()
        x_c, y_c, z_c = camera.GetPosition()
        p_w_c = np.array([
            [1, 0, 0, x_c],
            [0, -1, 0, y_c],
            [0, 0, -1, z_c],
            [0, 0, 0, 1],
        ])
        p_c = np.matmul(p_w_c, p.T).T  # x, y, z

        v_x_o, v_y_o, v_z_o = getActorXYZAxis(self.actor)
        v_x_c, v_y_c, v_z_c = np.identity(3)
        v_y_c, v_z_c = -v_y_c, -v_z_c
        # r_y is the angle between camera x-axis and object -y axis
        r_y = getAngle(-v_y_o, v_x_c)

        # theta is the angle between z_c and vector from camera to object
        v_c2o = np.array(self.actor.GetPosition()) - np.array(camera.GetPosition())
        theta = getAngle(v_c2o, v_z_c)
        alpha = r_y - theta

        l, t, r, b = self.getBBox2D()
        return [
            self.model_name, 0, 0, round(alpha, 2),
            l, t, r, b,  # bounding box 2d
            self.size[2], self.size[0], self.size[1],  # model height, width , length
            round(p_c[0, 0], 2), round(p_c[0, 1], 2), round(p_c[0, 2], 2),
            # location (x, y, z) in camera coordinate) different camera coordinate
            round(r_y, 2)
        ]


class ActorManager(QObject):
    signal_active_model = pyqtSignal(list)
    signal_highlight_model_list = pyqtSignal(str)
    signal_update_property_enter_scene = pyqtSignal(list)

    def __init__(self, render_window, interactor, bg_renderer):
        super(ActorManager, self).__init__()
        self.render_window = render_window
        self.interactor = interactor
        self.bg_renderer = bg_renderer
        # self.bg_renderer.GetActiveCamera()
        self.interactor.GetInteractorStyle().SetAutoAdjustCameraClippingRange(False)
        # self.bg_renderer.GetActiveCamera().SetClippingRange(0.00001, 1000000)
        self.actors = []

    def newActor(self, model_path, model_class, model_name, actor_id=0, actor_matrix=None, actor_size=[]):
        actor = Actor(self.render_window, self.interactor, model_path, model_class, model_name,
                      len(self.actors) + 1, actor_id)
        if actor_matrix is None and actor_size == []:
            # only copy the matrix of previous actors
            if len(self.actors) > 0 and self.actors[-1].model_path == actor.model_path:
                actor.setMatrix(self.actors[-1].actor.GetMatrix())
                actor.size = self.actors[-1].size
            else:
                # newPosition = list(actor.renderer.GetActiveCamera().GetPosition())
                # actor.actor.SetPosition(newPosition)
                # matrix = actor.renderer.GetActiveCamera().GetModelViewTransformMatrix()
                # actor.actor.SetOrigin(actor.actor.GetCenter())
                matrix = vtk.vtkMatrix4x4()
                actor.setMatrix(matrix)

                # Set the initial loading position of the model
                actor.actor.SetPosition([0, 0, float(SystemConfig.config_data["model"]["initial_position"])])
                actor.size = list(getActorXYZRange(actor.actor))
        else:
            # copy the camera matrix
            matrix = vtk.vtkMatrix4x4()
            matrix.DeepCopy(actor_matrix)
            # matrix.Invert()
            transform = getTransform(matrix)
            if actor.actor.GetUserMatrix() is not None:
                transform.GetMatrix(actor.actor.GetUserMatrix())
                actor.size = actor_size
            else:
                actor.actor.SetOrientation(transform.GetOrientation())
                actor.actor.SetPosition(transform.GetPosition())
                actor.actor.SetScale(transform.GetScale())
                actor.size = actor_size

        self.actors.append(actor)
        self.setActiveActor(-1)
        # list(self.InteractionProp.GetPosition() + self.InteractionProp.GetOrientation()) +
        # self.slabel.actor_manager.actors[-1].size
        # self.getCurrentActiveActor().Get

        if self.interactor.GetInteractorStyle().GetAutoAdjustCameraClippingRange():
            self.ResetCameraClippingRange()

        self.ResetCameraClippingRange()
        self.interactor.Render()

    def setActiveActor(self, index):
        """Set Active Actor by index.
        The specified actor will be moved to the last item

        Args:
            index (int): The index specified.
        """
        len_actors = len(self.actors)
        if len_actors == 0 or index < -len_actors or index >= len_actors:
            raise IndexError("index error")

        index %= len(self.actors)

        if index != len(self.actors) - 1:
            actor = self.actors[index]
            del self.actors[index]
            self.actors.append(actor)
            # highlight in the model list
            self.signal_highlight_model_list.emit(actor.model_path)

        self.render_window.SetNumberOfLayers(len(self.actors) + 1)

        for i, a in enumerate(self.actors):
            a.renderer.SetLayer(i + 1)
            # a.renderer.Render()

        renderer = self.actors[-1].renderer
        # very important for set the default render
        self.interactor.GetInteractorStyle().SetDefaultRenderer(renderer)
        self.interactor.GetInteractorStyle().SetCurrentRenderer(renderer)
        # if actor is not None:
        #     self.signal_active_model.emit(list(actor.actor.GetBounds()))

    # TODO: Remove the function
    def reformat(self):
        for a in self.actors:
            actor_matrix = deepCopyMatrix(a.actor.GetMatrix())
            actor_matrix.Invert()
            actor_transform = getTransform(actor_matrix)

            a.actor.SetUserMatrix(vtk.vtkMatrix4x4())
            # a.box_widget.SetTransform(vtk.vtkTransform())

            print(a.actor.GetBounds())
            camera = a.renderer.GetActiveCamera()
            camera.ApplyTransform(actor_transform)

    def getCurrentActiveActor(self):
        if len(self.actors) == 0:
            return None
        return self.actors[-1].actor

    def getCurrentActiveRenderer(self):
        return self.actors[-1].renderer

    def getIndex(self, actor):
        i = -1
        for i in reversed(range(len(self.actors))):
            if self.actors[i].actor is actor:
                break
        return i

    def clear(self):
        for a in self.actors:
            a.renderer.RemoveActor(a.actor)
            self.render_window.RemoveRenderer(a.renderer)
        self.actors = []

    def loadAnnotation(self, annotation_file):
        if not os.path.exists(annotation_file):
            return
        data = None
        with open(annotation_file, 'r') as f:
            data = json.load(f)

        return data

    def setCamera(self, camera_data):
        camera = self.bg_renderer.GetActiveCamera()
        camera.SetPosition(camera_data["position"])
        camera.SetFocalPoint(camera_data["focalPoint"])
        camera.SetViewAngle(camera_data["fov"])
        camera.SetViewUp(camera_data["viewup"])
        camera.SetDistance(camera_data["distance"])

    def ResetCameraClippingRange(self):
        bounds = []
        bounds += [self.bg_renderer.ComputeVisiblePropBounds()]
        bounds += [a.renderer.ComputeVisiblePropBounds() for a in self.actors]
        bound = []
        for i in range(6):
            if i % 2 == 0:
                bound += [min([b[i] for b in bounds])]
            else:
                bound += [max([b[i] for b in bounds])]

        # if there only an image
        if bound[-1] - bound[-2] == 0:
            bound[-1] = 0.5

        self.bg_renderer.ResetCameraClippingRange(bound)
        for a in self.actors:
            a.renderer.ResetCameraClippingRange(bound)

    def createActors(self, scene_folder, data):
        for i in range(data["model"]["num"]):
            model_path = os.path.join(scene_folder, data["model"][str(i)]["model_file"])

            if "actor_id" not in (data["model"][str(i)].keys()):
                data["model"][str(i)]["actor_id"] = 0

            self.newActor(model_path, data["model"][str(i)]["class"],
                          data["model"][str(i)]["class_name"],
                          data["model"][str(i)]["actor_id"],
                          data["model"][str(i)]["matrix"],
                          data["model"][str(i)]["size"]
                          )

            # updata property when enter a scene
            self.signal_update_property_enter_scene.emit(
                [self.actors[-1].actor_id] +
                list(self.getCurrentActiveActor().GetPosition() + self.getCurrentActiveActor().GetOrientation()) +
                self.actors[-1].size
            )

    def toJson(self, scene_folder):
        # self.reformat()
        # print info
        # for i, a in enumerate(self.actors):
        #     print("======{}======\n".format(i), a.actor.GetUserTransform().GetMatrix())
        #     print(a.renderer.GetActiveCamera().GetViewTransformMatrix())
        data = {"model": {}}
        data["model"]["num"] = len(self.actors)
        for i in range(len(self.actors)):
            data["model"]["{}".format(i)] = self.actors[i].toJson(scene_folder)
        return data

    @PyQt5.QtCore.pyqtSlot(list, bool)
    def update_camera(self, camera_data, is_change):
        if is_change is False:
            return
        camera = self.bg_renderer.GetActiveCamera()
        camera_position = [camera_data[0], camera_data[1], camera_data[2]]
        camera.SetPosition(camera_position)
        camera.SetViewAngle(camera_data[3])
        camera.SetDistance(camera_data[4])
        camera.SetViewUp([0, 1, 0])

        # Refresh the content in the field of view
        # self.slabel.actor_manager.ResetCameraClippingRange()
        # self.GetInteractor().Render()
        self.ResetCameraClippingRange()
        self.interactor.Render()

    def getEmptyJson(self, image_file):
        return {
            "image_file": image_file,
            "model": {"num": 0},
            "camera": {
                "matrix": SystemConfig.config_data["camera"]["matrix"],
                "position": SystemConfig.config_data["camera"]["position"],
                "focalPoint": SystemConfig.config_data["camera"]["focalPoint"],
                "fov": SystemConfig.config_data["camera"]["fov"],
                "viewup": SystemConfig.config_data["camera"]["viewup"],
                "distance": SystemConfig.config_data["camera"]["distance"]
            }
        }

    def delete_actor(self):
        if self.getCurrentActiveActor() is not None:
            a = self.actors[-1]
            a.renderer.RemoveActor(a.actor)
            self.render_window.RemoveRenderer(a.renderer)
            self.actors.pop()
            self.ResetCameraClippingRange()
            self.interactor.Render()
            self.interactor.GetInteractorStyle().resetHighlight()
