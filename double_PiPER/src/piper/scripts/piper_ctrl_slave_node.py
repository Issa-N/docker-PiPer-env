#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import rospy
from sensor_msgs.msg import JointState
from piper_sdk import Piper


class PiperSlaveNode:

    def __init__(self):

        rospy.init_node("piper_ctrl_slave_node")

        # =========================
        # params (launchから取得)
        # =========================
        self.can_port = rospy.get_param("~can_port", "can0")
        self.auto_enable = rospy.get_param("~auto_enable", True)
        self.gripper_exist = rospy.get_param("~gripper_exist", True)

        self.move_spd_rate_ctrl = 40

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

        rospy.loginfo("Slave ready. Waiting joint commands...")

        # =========================
        # Subscriber
        # =========================
        rospy.Subscriber(
            "joint_ctrl_single",   # ← remapされる
            JointState,
            self.joint_callback,
            queue_size=1
        )

    # =========================================================
    # Master追従
    # =========================================================
    def joint_callback(self, msg):

        if len(msg.position) < 7:
            return

        joints = list(msg.position[:6])
        gripper = msg.position[6]

        # safety clamp
        gripper = max(0.0, min(0.1, gripper))

        self.piper.move_j(joints, self.move_spd_rate_ctrl)

        if self.gripper_exist:
            self.piper.move_gripper(gripper, 1)


# =============================================================
if __name__ == "__main__":
    node = PiperSlaveNode()
    rospy.spin()
