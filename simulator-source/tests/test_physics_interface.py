import importlib.util
from pathlib import Path
import unittest

import mujoco
import numpy as np


MODULE_PATH = (
    Path(__file__).parents[1] / "libero" / "libero" / "envs" / "physics_interface.py"
)
SPEC = importlib.util.spec_from_file_location("libero_physics_interface", MODULE_PATH)
physics_interface = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(physics_interface)


class _FakeGripper:
    important_geoms = {
        "left_fingerpad": ["left_pad"],
        "right_fingerpad": ["right_pad"],
    }


class _FakeController:
    ee_ori_mat = np.eye(3)


class _FakeRobot:
    gripper = _FakeGripper()
    controller = _FakeController()
    ee_force = np.array([1.0, -2.0, 3.0])
    ee_torque = np.array([0.1, -0.2, 0.3])


class _FakeSim:
    def __init__(self, model, data):
        self.model = model
        self.data = data


class _FakeForceModel:
    actuator_forcerange = np.array([[-20.0, 20.0], [-20.0, 20.0], [-5.0, 5.0]])


class _FakeForceRobot:
    _ref_joint_gripper_actuator_indexes = [0, 1]


class MujocoPhysicsAdapterTest(unittest.TestCase):
    def test_observe_returns_cross_platform_physical_state(self):
        model = mujoco.MjModel.from_xml_string(
            """
            <mujoco>
              <option gravity="0 0 -9.81"/>
              <worldbody>
                <geom name="floor" type="plane" size="1 1 .1"/>
                <body name="left_finger" pos="0 0 .01">
                  <freejoint/>
                  <geom name="left_pad" type="box" size=".02 .02 .02" mass="1"/>
                </body>
                <body name="right_finger" pos=".2 0 .1">
                  <freejoint/>
                  <geom name="right_pad" type="box" size=".02 .02 .02" mass="1"/>
                </body>
              </worldbody>
            </mujoco>
            """
        )
        data = mujoco.MjData(model)
        for _ in range(20):
            mujoco.mj_step(model, data)

        state = physics_interface.MujocoPhysicsAdapter(
            _FakeSim(model, data), _FakeRobot()
        ).observe()

        vector = state.as_array()
        self.assertEqual(vector.shape, (physics_interface.PHYSICAL_STATE_DIM,))
        np.testing.assert_allclose(vector[:3], [1.0, -2.0, 3.0])
        np.testing.assert_allclose(vector[3:6], [0.1, -0.2, 0.3])
        self.assertGreater(vector[6], 0.0)
        self.assertEqual(vector[7], 0.0)
        self.assertGreater(vector[10], 0.0)
        self.assertEqual(vector[11], 1.0)

    def test_slip_velocity_is_object_relative_to_finger_regardless_of_contact_order(self):
        def observe_with_body_order(pad_first):
            bodies = {
                "pad": """
                    <body name="finger" pos="0 0 0">
                      <freejoint name="finger_joint"/>
                      <geom name="left_pad" type="box" size=".02 .02 .02" mass="1"/>
                    </body>
                """,
                "object": """
                    <body name="object" pos="0 0 .03">
                      <freejoint name="object_joint"/>
                      <geom name="object_geom" type="box" size=".02 .02 .02" mass="1"/>
                    </body>
                """,
            }
            order = ("pad", "object") if pad_first else ("object", "pad")
            model = mujoco.MjModel.from_xml_string(
                "<mujoco><option gravity='0 0 0'/><worldbody>"
                + "".join(bodies[name] for name in order)
                + "</worldbody></mujoco>"
            )
            data = mujoco.MjData(model)
            finger_joint = mujoco.mj_name2id(
                model, mujoco.mjtObj.mjOBJ_JOINT, "finger_joint"
            )
            data.qvel[model.jnt_dofadr[finger_joint] + 0] = 0.2
            mujoco.mj_forward(model, data)
            return physics_interface.MujocoPhysicsAdapter(
                _FakeSim(model, data), _FakeRobot()
            ).observe()

        pad_first = observe_with_body_order(True)
        pad_second = observe_with_body_order(False)

        np.testing.assert_allclose(pad_first.slip_velocity_xy, [-0.2, 0.0])
        np.testing.assert_allclose(pad_second.slip_velocity_xy, pad_first.slip_velocity_xy)


class MujocoGripForceControllerTest(unittest.TestCase):
    def test_normalized_command_sets_symmetric_force_limits_in_newtons(self):
        sim = _FakeSim(_FakeForceModel(), object())
        controller = physics_interface.MujocoGripForceController(
            sim, _FakeForceRobot(), force_range=(2.0, 18.0)
        )

        applied = controller.set_normalized_command(0.25)

        self.assertEqual(applied, 6.0)
        np.testing.assert_allclose(sim.model.actuator_forcerange[:2], [[-6.0, 6.0], [-6.0, 6.0]])
        np.testing.assert_allclose(sim.model.actuator_forcerange[2], [-5.0, 5.0])


if __name__ == "__main__":
    unittest.main()
