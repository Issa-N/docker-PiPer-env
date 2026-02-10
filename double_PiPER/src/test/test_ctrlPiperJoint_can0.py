#!/usr/bin/env python3
# -*-coding:utf8-*-
import time
import math
from piper_sdk import Piper

if __name__ == "__main__":

    move_spd_rate_ctrl = 40

    # ===== 円運動設定 =====
    # radius = 0.12
    radius = 0.15
    period = 2

    # ===== グリッパ設定 =====
    grip_min = 0.01      # 閉
    grip_max = 0.1   # 開（機種に合わせて調整）
    grip_period = 2.0 # 開閉周期

    dt = 0.01
    run_time = 10

    piper = Piper("can0")
    interface = piper.init()
    piper.connect()
    time.sleep(0.2)

    while not piper.enable_arm():
        time.sleep(0.01)

    piper.enable_gripper()

    interface.ModeCtrl(0x01, 0x01, move_spd_rate_ctrl, 0x00)

    print("Start circular motion with gripper...")

    base = list(piper.get_joint_states()[0])

    omega = 2 * math.pi / period
    grip_omega = 2 * math.pi / grip_period

    start = time.time()

    while time.time() - start < run_time:

        t = time.time() - start

        joints = base.copy()

        # ===== 円運動 =====
        joints[0] = base[0] + radius * math.cos(omega * t)
        joints[1] = base[1] + radius * math.sin(omega * t)
        # joints[2] = base[2] + radius * math.cos(omega * t)
        # joints[3] = base[3] + radius * math.sin(omega * t)
        # joints[4] = base[4] + radius * math.cos(omega * t)
        # joints[5] = base[5] + radius * math.sin(omega * t)

        piper.move_j(joints, move_spd_rate_ctrl)

        # ===== グリッパー開閉（sin波）=====
        g = (math.sin(grip_omega * t) + 1) / 2
        grip_pos = grip_min + g * (grip_max - grip_min)

        piper.move_gripper(grip_pos, 1)

        print("===================")
        print("Joint: ", joints)
        print("Gripper: ", grip_pos)
        print("===================\n\n")
        
        time.sleep(dt)

    print("Finished")
