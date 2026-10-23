# LIBERO-Pro Perturbation Reference

> Sources: `task_manifest.json`, BDDL `:perturbation_config` fields (`operator`/`variant`/`trigger`/`schedule`),
> and `CASE_MECHANISMS` in the runtime implementation, `nonphysical_perturbations.py`.

## Overview

- **Total task instances**: 1688 across four suites: `libero_10`, `libero_spatial`, `libero_object`, and `libero_goal`.
- **case_kind distribution**: 40 `base`, 863 `static`, and 785 `dynamic` instances.
- **case_id naming**: `Sxx` denotes a static perturbation, configured once at episode start and retained throughout the episode; `Dxx` denotes a dynamic perturbation, triggered conditionally during an episode.
- **Schedule rules** (from `:schedule_catalog`):
  - `static`: `(:start reset)` applies at reset; `(:duration episode)` lasts for the episode; `(:restore false)` disables restoration.
  - `dynamic`: `(:start event_trigger)` starts on an event; `(:duration case_defined)` and `(:restore case_defined)` use case-specific duration and restoration settings.

> For dynamic perturbations, `NonPhysicalPerturbationRuntime` checks `_dynamic_triggered` in
> `before_simulation_step` on every simulation step. Conditions include distance thresholds, grasp phases,
> contact, and task phases. Once triggered, the runtime modifies the scene, camera, obstacles, actions,
> lighting, or observations, and restores the applicable state at the event-window boundary or reset.

---

## Static Perturbations (S01–S22; 22 types)

| Case | Mechanism | Operator / Variant | Description |
|:----:|:----------|:-------------------|:------------|
| **S01** | pose | pose_transform / `xy_yaw` | Replace the target object's initial pose with another valid pose using XY translation and yaw. |
| **S02** | pose | pose_transform / `xy_yaw` | Replace the initial pose of the container or receiver. |
| **S03** | asset+pose | geometry_variant / `receiver_or_support_height` | Change the height of the receiver or support surface. |
| **S04** | pose | pose_transform / `planar_object_position_swap` | Swap the planar positions of two objects, subject to same_support_surface/collision_free/task_completable constraints. |
| **S05** | asset | geometry_variant / `restricted_approach_or_path` | Restrict the approach direction or traversal path with obstacle-like constraints. |
| **S06** | asset_replacement | asset_or_appearance / `same_class_or_unseen_instance` | Replace the target asset with a same-class or unseen instance. |
| **S07** | geometry | geometry_variant / `functional_part_geometry` | Change functional geometry such as openings, rims, or cavities. |
| **S08** | geometry | geometry_variant / `scale_or_aspect_ratio` | Change object scale or aspect ratio. |
| **S09** | geometry | geometry_variant / `container_opening_clearance_and_pose_coupling` | Change the coupling between container opening clearance and pose, subject to real_collision_geometry/full_containment/positive_clearance/insertion_depth constraints. |
| **S10** | asset | asset_or_appearance / `irrelevant_object_clutter` | Add objects unrelated to the task. |
| **S11** | asset | asset_or_appearance / `same_class_or_visually_similar_distractor` | Add same-class or visually similar distractors that can cause incorrect object selection. |
| **S12** | asset+occlusion | occlusion_or_obstacle / `persistent_front_occlusion` | Place a persistent occlusion screen in front of the target. |
| **S13** | appearance | asset_or_appearance / `color_texture_reflection_or_surface_state` | Change color, texture, reflectance, or surface state. |
| **S14** | appearance+lighting | asset_or_appearance / `foreground_background_contrast_or_scene_domain` | Change foreground/background contrast or the scene domain. |
| **S15** | camera | camera_transform / `fixed_extrinsics_or_cross_camera_calibration` | Change camera extrinsics through a fixed pose offset or cross-camera calibration. |
| **S16** | camera_intrinsics+observation | camera_transform / `intrinsics_fov_resolution_crop_or_distortion` | Change camera intrinsics, FOV, resolution, crop, or distortion. |
| **S17** | robot_state | state_or_language_event / `initial_joints_eef_orientation_or_gripper_opening` | Change initial joint angles, end-effector orientation, or gripper opening. |
| **S18** | calibration | state_or_language_event / `base_tcp_joint_zero_or_grasp_center_calibration` | Offset base, TCP, joint-zero, or grasp-center calibration. |
| **S19** | observation | observation_fault / `compression_noise_blur_exposure_contamination_or_depth_holes` | Corrupt observations through compression, noise, blur, exposure, contamination, or depth holes. |
| **S20** | action_timing+observation_timing | timing_or_action_fault / `fixed_rate_delay_or_action_window` | Apply fixed-rate delays or restricted action windows along the observation, inference, control, or action pipeline. |
| **S21** | language | state_or_language_event / `semantic_paraphrase` | Paraphrase the instruction while preserving its goal semantics. |
| **S22** | appearance | asset_or_appearance / `support_surface_texture_replacement` | Replace the workspace_surface texture while preserving collision_geometry_unchanged/friction_unchanged/object_poses_unchanged constraints; introduced in scheme v5. |

---

## Dynamic Perturbations (D01–D21; 21 identifiers including deleted D19)

The table retains the runtime identifiers, including the deleted D19 entry, for reference.

| Case | Mechanism | Operator / Variant / Trigger | Description |
|:----:|:----------|:------------------------------|:------------|
| **D01** | dynamic_pose | pose_transform / `xy_yaw_update` / trigger: **approach_or_pregrasp** | Move the target instantaneously during **approach/pregrasp**, triggered by the `trigger_distance_m` distance threshold. |
| **D02** | dynamic_pose | pose_transform / `xy_yaw_update` / trigger: **postgrasp_or_preplace** | Move the target **after grasping/before placement**. |
| **D03** | asset+dynamic_pose | occlusion_or_obstacle / `occupy_or_release_receiver` / trigger: **preplace** | Inject an obstacle to **occupy or release the receiver**. Variants include `occupy_or_release_receiver` and `persistent_triggered_receiver_occupation`; the latter persistently occupies the receiver when preconfigured in some tasks. |
| **D04** | asset+dynamic_pose+occlusion | occlusion_or_obstacle / `enter_hold_exit_occlusion` / trigger: **task_phase** | Introduce dynamic occlusion with a screen that **enters, holds, and exits**. |
| **D05** | asset+dynamic_pose | occlusion_or_obstacle / `obstacle_enters_path` / trigger: **transport** | Move an obstacle **into the robot's transport path**, with an alternative collision-free path remaining available. |
| **D06** | dynamic_pose | pose_transform / `distractor_move_or_local_rearrangement` / trigger: **task_phase** | **Move or locally rearrange distractors**, including cyclic displacement of multiple targets with nonpenetration checks. |
| **D07** | dynamic_camera | camera_transform / `shake_drift_or_persistent_offset` / trigger: **task_phase** | Apply camera **shake, drift, or a persistent offset**. |
| **D08** | observation | observation_fault / `camera_dropout_then_restore` / trigger: **task_phase** | Drop camera observations and then restore them. |
| **D09** | lighting+observation | observation_fault / `light_shadow_or_exposure_change` / trigger: **task_phase** | Change lighting, shadows, or exposure, restoring them after the event window. |
| **D10** | observation_timing | observation_fault / `drop_repeat_or_freeze_frames` / trigger: **task_phase** | Drop, repeat, or freeze frames. |
| **D11** | observation_timing | observation_fault / `timestamp_offset_or_state_freeze` / trigger: **task_phase** | Offset timestamps or freeze state observations. |
| **D12** | observation_timing | timing_or_action_fault / `transient_latency_spike` / trigger: **task_phase** | Introduce a transient latency spike in the observation/inference pipeline. |
| **D13** | action_timing | timing_or_action_fault / `delay_jitter_or_desynchronization` / trigger: **task_phase** | Introduce action delay jitter or desynchronization using event-specific delays. |
| **D14** | action_timing | timing_or_action_fault / `command_drop_or_repeat` / trigger: **task_phase** | Drop or repeat control commands. |
| **D15** | action_timing | timing_or_action_fault / `stale_chunk_late_chunk_or_replan_interrupt` / trigger: **state_change** | Use a stale or late action chunk, or interrupt replanning; duration is determined by stale_steps. |
| **D16** | action_takeover | state_or_language_event / `bounded_action_takeover_or_reachable_state_offset` / trigger: **task_phase** | Apply bounded action takeover or a reachable state offset without physical contact, for approximately 6 steps. |
| **D17** | state_event | state_or_language_event / `grasp_failure_result` / trigger: **grasp_attempt** | Simulate a failed grasp: on a grasp attempt detected by closing plus contact, release or retract the object from the gripper, with an approximately 40-step failure window. |
| **D18** | state_event | state_or_language_event / `reachable_collision_free_drop_state` / trigger: **transport** | Cause a **reachable, collision-free object drop** during transport while keeping recovery possible. |
| **D19 (Deleted)** | state_event | state_or_language_event / `misplace_partial_insert_or_wrong_receiver_result` / trigger: **place_attempt** | Introduce **misplacement, partial insertion, or placement into the wrong receiver**, while keeping correction possible. |
| **D20** | robot_state | pose_transform / `collision_induced_reachable_joint_displacement` / trigger: **robot_in_motion** | Apply collision-induced reachable joint displacement while the robot moves, triggered by end-effector displacement and action norm. Constraints: single_trigger/joint_limits/collision_free/no_self_collision/workspace_clearance; introduced in scheme v5. |
| **D21** | language | state_or_language_event / `equivalent_restatement_or_clarification` / trigger: **task_phase** | **Restate or clarify** the instruction during execution while preserving its goal semantics. |

---

### Notes

- The default dynamic **event window is approximately 24 steps** (`EVENT_START=48` to `EVENT_END=72`). Case-specific overrides include D14=24, D16=6, D17=40, and D15 as determined by `chunk_size`/`stale_chunk_steps`.
- Displacement-based dynamic perturbations (D01/D02/D06/D18/D19) **teleport objects** after collision checks through `_safe_offset_pose`. D17 is a `grasp_failure` state event; D07/D09 restore camera/lighting snapshots at the end of the window.
