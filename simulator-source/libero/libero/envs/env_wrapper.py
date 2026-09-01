import os
import numpy as np
import robosuite as suite
import matplotlib.cm as cm

from robosuite.utils.errors import RandomizationError

import libero.libero.envs.bddl_utils as BDDLUtils
from libero.libero.envs import *
from libero.libero.envs.nonphysical_perturbations import describe_execution_plan


def _task_compatible_init_state(env, mujoco_state):
    """Merge one task-local injected free joint into a BASE init state."""

    plan = getattr(env, "perturbation_plan", None)
    params = getattr(plan, "params", {}) if plan is not None else {}
    if not (
        getattr(plan, "case_id", None) == "D03"
        and bool(params.get("persistent_movable_asset", False))
    ):
        return mujoco_state

    incoming = np.asarray(mujoco_state, dtype=np.float64).reshape(-1)
    current = np.asarray(env.sim.get_state().flatten(), dtype=np.float64)
    if incoming.size == current.size:
        return mujoco_state

    obstacle = env.perturbation_runtime._persistent_d03_obstacle_name()
    scene_object = getattr(env, "objects_dict", {}).get(obstacle)
    joints = list(getattr(scene_object, "joints", []) or [])
    free_joints = []
    for joint in joints:
        joint_id = int(env.sim.model.joint_name2id(joint))
        if int(env.sim.model.jnt_type[joint_id]) == 0:
            free_joints.append(joint_id)
    if len(free_joints) != 1:
        raise ValueError(
            "D03 persistent_movable_asset init compatibility requires one free joint"
        )

    joint_id = free_joints[0]
    qpos_address = int(env.sim.model.jnt_qposadr[joint_id])
    dof_address = int(env.sim.model.jnt_dofadr[joint_id])
    new_nq = int(env.sim.model.nq)
    new_nv = int(env.sim.model.nv)
    old_nq = new_nq - 7
    old_nv = new_nv - 6
    old_tail = 1 + old_nq + old_nv
    new_tail = 1 + new_nq + new_nv
    if (
        old_nq < 0
        or old_nv < 0
        or incoming.size - old_tail != current.size - new_tail
    ):
        raise ValueError(
            "D03 persistent_movable_asset init state must differ by one free joint"
        )

    merged = current.copy()
    merged[0] = incoming[0]
    old_qpos = incoming[1 : 1 + old_nq]
    merged[1 : 1 + qpos_address] = old_qpos[:qpos_address]
    merged[1 + qpos_address + 7 : 1 + new_nq] = old_qpos[qpos_address:]
    old_qvel = incoming[1 + old_nq : old_tail]
    qvel_start = 1 + new_nq
    merged[qvel_start : qvel_start + dof_address] = old_qvel[:dof_address]
    merged[qvel_start + dof_address + 6 : new_tail] = old_qvel[dof_address:]
    merged[new_tail:] = incoming[old_tail:]
    return merged


class ControlEnv:
    def __init__(
        self,
        bddl_file_name,
        robots=["Panda"],
        controller="OSC_POSE",
        gripper_types="default",
        initialization_noise=None,
        use_camera_obs=True,
        has_renderer=False,
        has_offscreen_renderer=True,
        render_camera="frontview",
        render_collision_mesh=False,
        render_visual_mesh=True,
        render_gpu_device_id=-1,
        control_freq=20,
        horizon=1000,
        ignore_done=False,
        hard_reset=True,
        camera_names=[
            "agentview",
            "robot0_eye_in_hand",
        ],
        camera_heights=128,
        camera_widths=128,
        camera_depths=False,
        camera_segmentations=None,
        renderer="mujoco",
        renderer_config=None,
        max_reset_attempts=50,
        **kwargs,
    ):
        assert os.path.exists(
            bddl_file_name
        ), f"[error] {bddl_file_name} does not exist!"

        controller_configs = suite.load_controller_config(default_controller=controller)

        problem_info = BDDLUtils.get_problem_info(bddl_file_name)
        # Check if we're using a multi-armed environment and use env_configuration argument if so

        # Create environment
        self.problem_name = problem_info["problem_name"]
        self.domain_name = problem_info["domain_name"]
        self._base_language_instruction = problem_info["language_instruction"]
        self.max_reset_attempts = int(max_reset_attempts)
        if self.max_reset_attempts <= 0:
            raise ValueError("max_reset_attempts must be positive")
        self.env = TASK_MAPPING[self.problem_name](
            bddl_file_name,
            robots=robots,
            controller_configs=controller_configs,
            gripper_types=gripper_types,
            initialization_noise=initialization_noise,
            use_camera_obs=use_camera_obs,
            has_renderer=has_renderer,
            has_offscreen_renderer=has_offscreen_renderer,
            render_camera=render_camera,
            render_collision_mesh=render_collision_mesh,
            render_visual_mesh=render_visual_mesh,
            render_gpu_device_id=render_gpu_device_id,
            control_freq=control_freq,
            horizon=horizon,
            ignore_done=ignore_done,
            hard_reset=hard_reset,
            camera_names=camera_names,
            camera_heights=camera_heights,
            camera_widths=camera_widths,
            camera_depths=camera_depths,
            camera_segmentations=camera_segmentations,
            renderer=renderer,
            renderer_config=renderer_config,
            **kwargs,
        )

    @property
    def obj_of_interest(self):
        return self.env.obj_of_interest

    def step(self, action):
        return self.env.step(action)

    def step_with_gripper_force(self, action, force_command):
        return self.env.step_with_gripper_force(action, force_command)

    def reset(self):
        last_error = None
        for _ in range(self.max_reset_attempts):
            try:
                return self.env.reset()
            except RandomizationError as exc:
                last_error = exc
        raise RandomizationError(
            f"Failed to reset after {self.max_reset_attempts} placement attempts"
        ) from last_error

    @property
    def language_instruction(self):
        if hasattr(self.env, "language_instruction"):
            return self.env.language_instruction
        return self._base_language_instruction

    def check_success(self):
        return self.env._check_success()

    @property
    def _visualizations(self):
        return self.env._visualizations

    @property
    def robots(self):
        return self.env.robots

    @property
    def sim(self):
        return self.env.sim

    def get_sim_state(self):
        return self.env.sim.get_state().flatten()

    def _post_process(self):
        return self.env._post_process()

    def _update_observables(self, force=False):
        self.env._update_observables(force=force)

    def set_state(self, mujoco_state):
        self.env.sim.set_state_from_flattened(mujoco_state)

    def reset_from_xml_string(self, xml_string):
        self.env.reset_from_xml_string(xml_string)

    def seed(self, seed):
        self.env.seed(seed)

    def set_perturbation_seed(self, seed):
        self.env.perturbation_runtime.set_seed(seed)

    def get_perturbation_plan(self):
        plan = self.env.perturbation_plan
        runtime = self.env.perturbation_runtime
        return describe_execution_plan(
            plan, runtime.seed, runtime.event_duration_steps
        )

    def set_init_state(self, init_state):
        return self.regenerate_obs_from_state(init_state)

    def set_gripper_force_command(self, command):
        return self.env.set_gripper_force_command(command)

    def begin_perturbation_rollout(self):
        self.env.perturbation_runtime.begin_rollout(self.env)
        self.env._perturbation_step = 0
        self._update_observables(force=True)
        obs = self.env._get_observations()
        return self.env.perturbation_runtime.transform_observation(obs, 0)

    def regenerate_obs_from_state(self, mujoco_state):
        self.env.perturbation_runtime.prepare_reset(self.env)
        self.set_state(_task_compatible_init_state(self.env, mujoco_state))
        self.env.sim.forward()
        self.env._perturbation_step = 0
        self.env.perturbation_runtime.reset()
        self.env.perturbation_runtime.apply_static(self.env)
        if (
            self.env.perturbation_plan.case_id != "BASE"
            and self.env._check_success()
        ):
            raise RuntimeError(
                f"Perturbation {self.env.perturbation_plan.case_id} "
                "makes the task successful after loading its initial state"
            )
        self.check_success()
        self._post_process()
        self._update_observables(force=True)
        obs = self.env._get_observations()
        return self.env.perturbation_runtime.transform_observation(obs, 0)

    def close(self):
        self.env.close()
        del self.env


class OffScreenRenderEnv(ControlEnv):
    """
    For visualization and evaluation.
    """

    def __init__(self, **kwargs):
        # This shouldn't be customized
        kwargs["has_renderer"] = False
        kwargs["has_offscreen_renderer"] = True
        super().__init__(**kwargs)


class SegmentationRenderEnv(OffScreenRenderEnv):
    """
    This wrapper will additionally generate the segmentation mask of objects,
    which is useful for comparing attention.
    """

    def __init__(
        self,
        camera_segmentations="instance",
        camera_heights=128,
        camera_widths=128,
        **kwargs,
    ):
        assert camera_segmentations is not None
        kwargs["camera_segmentations"] = camera_segmentations
        kwargs["camera_heights"] = camera_heights
        kwargs["camera_widths"] = camera_widths
        self.segmentation_id_mapping = {}
        self.instance_to_id = {}
        self.segmentation_robot_id = None
        super().__init__(**kwargs)

    def step(self, action):
        return self.env.step(action)

    def reset(self):
        obs = self.env.reset()
        self.segmentation_id_mapping = {}

        for i, instance_name in enumerate(list(self.env.model.instances_to_ids.keys())):
            if instance_name == "Panda0":
                self.segmentation_robot_id = i

        for i, instance_name in enumerate(list(self.env.model.instances_to_ids.keys())):
            if instance_name not in ["Panda0", "RethinkMount0", "PandaGripper0"]:
                self.segmentation_id_mapping[i] = instance_name

        self.instance_to_id = {
            v: k + 1 for k, v in self.segmentation_id_mapping.items()
        }
        return obs

    def get_segmentation_instances(self, segmentation_image):
        # get all instances' segmentation separately
        seg_img_dict = {}
        segmentation_image[segmentation_image > self.segmentation_robot_id] = (
            self.segmentation_robot_id + 1
        )
        seg_img_dict["robot"] = segmentation_image * (
            segmentation_image == self.segmentation_robot_id + 1
        )

        for seg_id, instance_name in self.segmentation_id_mapping.items():
            seg_img_dict[instance_name] = segmentation_image * (
                segmentation_image == seg_id + 1
            )
        return seg_img_dict

    def get_segmentation_of_interest(self, segmentation_image):
        # get the combined segmentation of obj of interest
        # 1 for obj_of_interest
        # -1.0 for robot
        # 0 for other things
        ret_seg = np.zeros_like(segmentation_image)
        for obj in self.obj_of_interest:
            ret_seg[segmentation_image == self.instance_to_id[obj]] = 1.0
        # ret_seg[segmentation_image == self.segmentation_robot_id+1] = -1.0
        ret_seg[segmentation_image == 0] = -1.0
        return ret_seg

    def segmentation_to_rgb(self, seg_im, random_colors=False):
        """
        Helper function to visualize segmentations as RGB frames.
        NOTE: assumes that geom IDs go up to 255 at most - if not,
        multiple geoms might be assigned to the same color.
        """
        # ensure all values lie within [0, 255]
        seg_im = np.mod(seg_im, 256)

        if random_colors:
            colors = randomize_colors(N=256, bright=True)
            return (255.0 * colors[seg_im]).astype(np.uint8)
        else:
            # deterministic shuffling of values to map each geom ID to a random int in [0, 255]
            rstate = np.random.RandomState(seed=2)
            inds = np.arange(256)
            rstate.shuffle(inds)
            seg_img = (
                np.array(255.0 * cm.rainbow(inds[seg_im], 10))
                .astype(np.uint8)[..., :3]
                .astype(np.uint8)
                .squeeze(-2)
            )
            print(seg_img.shape)
            cv2.imshow("Seg Image", seg_img[::-1])
            cv2.waitKey(1)
            # use @inds to map each geom ID to a color
            return seg_img


class DemoRenderEnv(ControlEnv):
    """
    For visualization and evaluation.
    """

    def __init__(self, **kwargs):
        # This shouldn't be customized
        kwargs["has_renderer"] = False
        kwargs["has_offscreen_renderer"] = True
        kwargs["render_camera"] = "frontview"

        super().__init__(**kwargs)

    def _get_observations(self):
        return self.env._get_observations()
