#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import rospy
import math
import numpy as np
from sensor_msgs.msg import JointState
from piper_msgs.msg import PiperEulerPose
from piper_sdk import Piper



class PiperSlaveNode:

    def __init__(self):

        rospy.init_node("piper_ctrl_slave_node")

        # =========================
        # params
        # =========================
        self.can_port = rospy.get_param("~can_port", "can0")
        self.auto_enable = rospy.get_param("~auto_enable", True)
        self.gripper_exist = rospy.get_param("~gripper_exist", True)

        self.move_spd_rate_ctrl = 40

        # =========================
        # Workspace limit (meters)
        # =========================
        self.workspace = {
            "x_min":  -0.05,
            "x_max":   0.05,
            "y_min":  -0.32,
            "y_max":   0.32,
            "z_min":   0.1,
            "z_max":   0.55,
            "rz_min": -3.0,
            "rz_max":  3.0,
        }
        # self.workspace = {
        #     "x_min": -math.inf,
        #     "x_max":  math.inf,
        #     "y_min": -math.inf,
        #     "y_max":  math.inf,
        #     "z_min": -math.inf,
        #     "z_max":  math.inf,
        # }

        # 最新のleader姿勢保存用
        self.latest_pose = None

        # =========================
        # Piper init
        # =========================
        self.piper = Piper(self.can_port)
        self.interface = self.piper.init()

        self.piper.connect()
        time.sleep(0.2)

        if self.auto_enable:
            while not self.piper.enable_arm():
                time.sleep(0.01)

            if self.gripper_exist:
                self.piper.enable_gripper()

        self.interface.ModeCtrl(0x01, 0x01, self.move_spd_rate_ctrl, 0x00)

        rospy.loginfo("Left Slave ready.")

        # =========================
        # Subscribers
        # =========================
        rospy.Subscriber(
            "joint_ctrl_single",
            JointState,
            self.joint_callback,
            queue_size=1
        )

        rospy.Subscriber(
            "/end_pose_euler",
            PiperEulerPose,
            self.pose_callback,
            queue_size=1
        )

    # =========================================================
    # leaderのエンド姿勢を保存
    # =========================================================
    def pose_callback(self, msg):
        self.latest_pose = msg
        # print("===== Leader End Pose =====")
        # print("x: {:.3f}  y: {:.3f}  z: {:.3f}".format(msg.x, msg.y, msg.z))
        # print("roll: {:.3f}  pitch: {:.3f}  yaw: {:.3f}".format(
        #     msg.roll, msg.pitch, msg.yaw))
        # print("===========================")
    
    # =========================================================
    # 動作可能領域をロボット基準座標系→World座標系に変換
    # =========================================================
    def transform_point(p2, rx, ry, rz, t=None, degrees=False):
        """
        p2 : 座標系2での点 [x, y, z]
        rx, ry, rz : roll, pitch, yaw (ZYX順)
        t : 並進ベクトル [tx, ty, tz]
        degrees : 角度がdegreeならTrue
        """

        if degrees:
            rx = np.deg2rad(rx)
            ry = np.deg2rad(ry)
            rz = np.deg2rad(rz)

        # 回転行列
        Rx = np.array([
            [1, 0, 0],
            [0, np.cos(rx), -np.sin(rx)],
            [0, np.sin(rx),  np.cos(rx)]
        ])

        Ry = np.array([
            [ np.cos(ry), 0, np.sin(ry)],
            [0, 1, 0],
            [-np.sin(ry), 0, np.cos(ry)]
        ])

        Rz = np.array([
            [np.cos(rz), -np.sin(rz), 0],
            [np.sin(rz),  np.cos(rz), 0],
            [0, 0, 1]
        ])

        # ZYX順
        R = Rz @ Ry @ Rx

        p2 = np.array(p2)

        if t is None:
            t = np.zeros(3)
        else:
            t = np.array(t)

        # 座標変換
        pB = R @ p2 + t

        return pB

    # =========================================================
    # workspace内判定
    # =========================================================
    def is_inside_workspace(self, pose):

        x = pose.x
        y = pose.y
        z = pose.z
        rz_rad = abs(abs(pose.yaw)-0.663)
        # print("yow:", abs(abs(pose.yaw)-0.663))
        # print("marg:",1/math.cos(rz_rad))#, math.cos(rz))
        # print("rx:", pose.roll)
        # print("ry:", pose.pitch)

        # transform_point(p2, rx, ry, rz, t=None, degrees=False)


        # if not (self.workspace["x_min"]/math.cos(rz_rad) <= x <= self.workspace["x_max"]/math.cos(rz_rad)):
        #     return False
        if not (self.workspace["y_min"]/math.cos(rz_rad) <= y <= self.workspace["y_max"]/math.cos(rz_rad)):
            return False
        # if not (self.workspace["x_min"] <= x <= self.workspace["x_max"]):
        #         return False
        # if not (self.workspace["y_min"] <= y <= self.workspace["y_max"]/math.cos(rz_rad)):
        #     return False
        # if not (self.workspace["z_min"] <= z <= self.workspace["z_max"]):
        #     return False

        return True

    # =========================================================
    # Master追従
    # =========================================================
    def joint_callback(self, msg):

        # leader姿勢がまだ来ていない場合は動かさない
        if self.latest_pose is None:
            return

        # workspace外なら動かない
        if not self.is_inside_workspace(self.latest_pose):
            rospy.logwarn_throttle(1.0, "Left Arm: Outside workspace. Motion blocked.")
            return

        if len(msg.position) < 7:
            return

        joints = list(msg.position[:6])
        gripper = msg.position[6]

        # gripper safety clamp
        gripper = max(0.0, min(0.1, gripper))

        # ======= 動作実行 =======
        self.piper.move_j(joints, self.move_spd_rate_ctrl)

        if self.gripper_exist:
            self.piper.move_gripper(gripper, 1)

        ## debug
        # print("=======================")
        # print(self.piper.get_end_pose_euler()[0])
        # print("=======================")


# =============================================================
if __name__ == "__main__":
    node = PiperSlaveNode()
    rospy.spin()