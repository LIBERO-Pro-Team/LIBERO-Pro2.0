from dataclasses import dataclass

import mujoco
import numpy as np


PHYSICAL_STATE_DIM = 12
PHYSICAL_STATE_KEY = "robot0_physics"


@dataclass(frozen=True)
class PhysicalState:
    """Robot-centric physical feedback in SI units.

    Force and torque are expressed in the end-effector frame. Slip velocity is
    the force-weighted relative contact velocity in that frame's XY plane.
    """

    wrist_force: np.ndarray
    wrist_torque: np.ndarray
    finger_normal_force: np.ndarray
    slip_velocity_xy: np.ndarray
    contact_confidence: float
    sensor_valid: float

    def as_array(self) -> np.ndarray:
        state = np.concatenate(
            [
                np.asarray(self.wrist_force, dtype=np.float32).reshape(3),
                np.asarray(self.wrist_torque, dtype=np.float32).reshape(3),
                np.asarray(self.finger_normal_force, dtype=np.float32).reshape(2),
                np.asarray(self.slip_velocity_xy, dtype=np.float32).reshape(2),
                np.asarray([self.contact_confidence, self.sensor_valid], dtype=np.float32),
            ]
        )
        if state.shape != (PHYSICAL_STATE_DIM,):
            raise ValueError(f"Expected {PHYSICAL_STATE_DIM} physical values, got {state.shape}")
        return state


class MujocoGripForceController:
    """Map a normalized command to the gripper actuator force limits."""

    def __init__(self, sim, robot, force_range=(2.0, 20.0)):
        minimum, maximum = (float(value) for value in force_range)
        if not 0 <= minimum < maximum:
            raise ValueError("gripper_force_range must satisfy 0 <= minimum < maximum")
        self._sim = sim
        self._force_range = (minimum, maximum)
        self._actuator_ids = tuple(
            int(index) for index in robot._ref_joint_gripper_actuator_indexes
        )
        if not self._actuator_ids:
            raise ValueError("The robot has no gripper actuators")

    def set_normalized_command(self, command):
        command = float(np.asarray(command).reshape(()))
        if not np.isfinite(command):
            raise ValueError("Gripper force command must be finite")
        command = float(np.clip(command, 0.0, 1.0))
        minimum, maximum = self._force_range
        force_limit = minimum + command * (maximum - minimum)
        self._sim.model.actuator_forcerange[list(self._actuator_ids)] = (-force_limit, force_limit)
        return force_limit


class MujocoPhysicsAdapter:
    """Translate MuJoCo and robosuite state into :class:`PhysicalState`."""

    def __init__(self, sim, robot, contact_force_scale=1.0):
        self._sim = sim
        self._robot = robot
        self._contact_force_scale = float(contact_force_scale)
        if self._contact_force_scale <= 0:
            raise ValueError("contact_force_scale must be positive")

        self._model = getattr(sim.model, "_model", sim.model)
        self._data = getattr(sim.data, "_data", sim.data)
        important_geoms = robot.gripper.important_geoms
        self._left_pad_ids = self._geom_ids(important_geoms.get("left_fingerpad", []))
        self._right_pad_ids = self._geom_ids(important_geoms.get("right_fingerpad", []))
        self._pad_geometry_valid = bool(self._left_pad_ids and self._right_pad_ids)

    def observe(self) -> PhysicalState:
        wrist_force, force_valid = self._robot_vector("ee_force")
        wrist_torque, torque_valid = self._robot_vector("ee_torque")
        finger_force = np.zeros(2, dtype=np.float64)
        weighted_slip = np.zeros(2, dtype=np.float64)
        total_weight = 0.0

        eef_rotation, rotation_valid = self._robot_rotation()
        for contact_id in range(int(self._data.ncon)):
            contact = self._data.contact[contact_id]
            finger_contact = self._finger_contact(int(contact.geom1), int(contact.geom2))
            if finger_contact is None:
                continue
            finger_index, finger_geom, object_geom = finger_contact

            wrench = np.zeros(6, dtype=np.float64)
            mujoco.mj_contactForce(self._model, self._data, contact_id, wrench)
            normal_force = abs(float(wrench[0]))
            if not np.isfinite(normal_force):
                continue

            finger_force[finger_index] += normal_force
            relative_velocity = self._relative_geom_velocity(
                finger_geom, object_geom, np.asarray(contact.pos, dtype=np.float64)
            )
            if not np.all(np.isfinite(relative_velocity)):
                continue
            slip_xy = eef_rotation.T.dot(relative_velocity)[:2]
            weighted_slip += normal_force * slip_xy
            total_weight += normal_force

        slip_velocity = weighted_slip / total_weight if total_weight > 0 else weighted_slip
        confidence = min(1.0, total_weight / self._contact_force_scale)
        valid = float(
            force_valid
            and torque_valid
            and self._pad_geometry_valid
            and rotation_valid
        )
        return PhysicalState(
            wrist_force=wrist_force,
            wrist_torque=wrist_torque,
            finger_normal_force=finger_force,
            slip_velocity_xy=slip_velocity,
            contact_confidence=confidence,
            sensor_valid=valid,
        )

    def _geom_ids(self, names):
        ids = set()
        for name in names:
            try:
                if hasattr(self._sim.model, "geom_name2id"):
                    geom_id = self._sim.model.geom_name2id(name)
                else:
                    geom_id = mujoco.mj_name2id(self._model, mujoco.mjtObj.mjOBJ_GEOM, name)
            except (KeyError, ValueError):
                continue
            if geom_id >= 0:
                ids.add(int(geom_id))
        return ids

    def _finger_contact(self, geom1, geom2):
        all_pad_ids = self._left_pad_ids | self._right_pad_ids
        if geom1 in all_pad_ids and geom2 in all_pad_ids:
            return None
        for finger_index, pad_ids in enumerate((self._left_pad_ids, self._right_pad_ids)):
            if geom1 in pad_ids:
                return finger_index, geom1, geom2
            if geom2 in pad_ids:
                return finger_index, geom2, geom1
        return None

    def _relative_geom_velocity(self, finger_geom, object_geom, contact_position):
        finger_velocity = self._geom_point_velocity(finger_geom, contact_position)
        object_velocity = self._geom_point_velocity(object_geom, contact_position)
        return object_velocity - finger_velocity

    def _geom_point_velocity(self, geom_id, point):
        velocity = np.zeros(6, dtype=np.float64)
        mujoco.mj_objectVelocity(
            self._model, self._data, mujoco.mjtObj.mjOBJ_GEOM, int(geom_id), velocity, 0
        )
        offset = point - np.asarray(self._data.geom_xpos[int(geom_id)], dtype=np.float64)
        return velocity[3:] + np.cross(velocity[:3], offset)

    def _robot_vector(self, name):
        try:
            value = np.asarray(getattr(self._robot, name), dtype=np.float64).reshape(3)
        except (AttributeError, KeyError, TypeError, ValueError):
            return np.zeros(3, dtype=np.float64), False
        return (value, True) if np.all(np.isfinite(value)) else (np.zeros(3), False)

    def _robot_rotation(self):
        try:
            value = np.asarray(
                self._robot.controller.ee_ori_mat, dtype=np.float64
            ).reshape(3, 3)
        except (AttributeError, KeyError, TypeError, ValueError):
            return np.eye(3, dtype=np.float64), False
        return (value, True) if np.all(np.isfinite(value)) else (np.eye(3), False)
