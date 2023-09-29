import os
import sys
import math
import string
import bpy
from . utils import *
from enum import Enum

class OBJECT_TYPE(Enum):
    THING = 0
    ARMATURE = 1
    GENERIC_ARMATURE = 2

class BONE_NAME(Enum):
    HEAD = "Head"
    ROOT = "Root"
    TAIL1 = "Tail1"
    TAIL2 = "Tail2"
    TAIL3 = "Tail3"
    TAIL4 = "Tail4"
    TAIL5 = "Tail5"
    TAIL6 = "Tail6"
    TAIL7 = "Tail7"
    TAIL8 = "Tail8"
    SPINE1 = "Spine"
    SPINE2 = "Spine1"
    SPINE3 = "Spine2"
    NECK = "Neck"
    EYEBROWS = "Eyebrows"
    SHOULDER_L = "LeftShoulder"
    UPPER_ARM_L = "LeftArm"
    LOWER_ARM_L = "LeftForeArm"
    HAND_L = "LeftHand"
    EAR1_L = "LeftEar1"
    EAR2_L = "LeftEar2"
    FINGER1_L = "LeftFinger1"
    FINGER2_L = "LeftFinger2"
    FINGER3_L = "LeftFinger3"
    THUMB1_L = "LeftThumb1"
    THUMB2_L = "LeftThumb2"
    HIP_JOINT_L = "LeftHipJoint"
    UPPER_LEG_L = "LeftUpLeg"
    LOWER_LEG_L = "LeftLeg"
    FOOT_L = "LeftFoot"
    TOE_L = "LeftToe"
    IK_LEG_POLE_L = "IKLegPole.L"
    IK_LEG_TARGET_L = "IKLegTarget.L"
    IK_FRONT_LEG_POLE_L = "IKFrontLegPole.L"
    IK_FRONT_LEG_TARGET_L = "IKFrontLegTarget.L"
    IK_TAIL_POLE = "IKTailPole"
    IK_TAIL_TARGET = "IKTailTarget"

    SHOULDER_R = "RightShoulder"
    UPPER_ARM_R = "RightArm"
    LOWER_ARM_R = "RightForeArm"
    HAND_R = "RightHand"
    FINGER1_R = "RightFinger1"
    FINGER2_R = "RightFinger2"
    FINGER3_R = "RightFinger3"
    THUMB1_R = "RightThumb1"
    THUMB2_R = "RightThumb2"
    HIP_JOINT_R = "RightHipJoint"
    UPPER_LEG_R = "RightUpLeg"
    LOWER_LEG_R = "RightLeg"
    FOOT_R = "RightFoot"
    IK_LEG_POLE_R = "RightIKLegPole"
    IK_LEG_TARGET_R = "RightIKLegTarget"

class WIZ_OT_base_armature(bpy.types.Operator):
    bl_label = "Simple operator"
    bl_idname = "view3d.add_armature"
    bl_description = "Add an armature to the selected object"

    def set_object_mode():
        if bpy.context.active_object and bpy.context.active_object.mode == 'EDIT':
            bpy.ops.object.editmode_toggle()
        if bpy.context.active_object and bpy.context.active_object.mode == 'POSE':
            bpy.ops.object.posemode_toggle()

    def set_edit_mode():
        if bpy.context.active_object and not bpy.context.active_object.mode == 'EDIT':
            bpy.ops.object.editmode_toggle()

    def set_pose_mode():
        if bpy.context.active_object and not bpy.context.active_object.mode == 'POSE':
            bpy.ops.object.posemode_toggle()

    def get_mesh_and_armature():
        selected_objects = bpy.context.selected_objects

        if not selected_objects or 1 < len(selected_objects) > 2:
            info("Please select a mesh to assign")
            return None, None

        if len(selected_objects) == 1:
            if selected_objects[0].type != "MESH":
                info(f"Please select a mesh not a {selected_objects[0].type}")
                return None, None

            # Armature not supplied, so find it
            armatures = [ob for ob in bpy.context.scene.objects if ob.type == "ARMATURE"]
            if len(armatures) != 1:
                info(f"Please also select an armature to pair with")
                return None, None

            return (selected_objects[0], armatures[0])

        elif (selected_objects[0].type != "ARMATURE" and selected_objects[1].type != "ARMATURE") or \
            (selected_objects[0].type != "MESH" and selected_objects[1].type != "MESH"):
            info("Please select an armature and a mesh")
            return None, None

        armature = selected_objects[0] if selected_objects[0].type == "ARMATURE" else selected_objects[1]
        mesh = selected_objects[1] if selected_objects[0].type == "ARMATURE" else selected_objects[0]

        return (mesh, armature)

    def assign_arm_to_mesh(arm):
        # Ensure the armature is the active object so the other meshes get stored under it
        bpy.context.view_layer.objects.active = arm

        # Parent with automatic weights
        bpy.ops.object.parent_set(type="ARMATURE_AUTO")
        WIZ_OT_base_armature.set_pose_mode()
        bpy.ops.pose.select_all(action="SELECT")
        bpy.ops.pose.armature_apply(selected=False)


    def add_armature(
        location,
        radius: float):

        bpy.ops.object.armature_add(
            radius=radius,
            enter_editmode=True,
            align='WORLD',
            location=location,
            rotation=(0.0, 0.0, 0.0),
            scale=(0.0, 0.0, 0.0))

        bpy.context.active_bone.name = BONE_NAME.ROOT.value

        bpy.context.active_object.show_in_front = True
        bpy.context.active_object["godot_object_type"] = OBJECT_TYPE.ARMATURE.name
        return bpy.context.active_object

    def add_bone(name: str, location):

        bpy.ops.armature.extrude_move(
            ARMATURE_OT_extrude={
                "forked":False},
            TRANSFORM_OT_translate={
                "value":location,
                "constraint_axis":(False, False, False),
                "mirror":False,
                "snap":False,
                "snap_target":'CLOSEST',
                "snap_point":(0, 0, 0),
                "snap_align":False,
                "snap_normal":(0, 0, 0),
                "gpencil_strokes":False,
                "texture_space":False,
                "remove_on_cancel":False,
                "release_confirm":False,
                "use_accurate":False})

        bone = bpy.context.active_bone
        bone.name = name
        bone.roll = 0

        return bone

    def detach_bone(
        bone,
        head_offset = (0, 0, 0),
        clear_parent = False):

        bone.select = True
        bpy.ops.armature.parent_clear(type='CLEAR' if clear_parent else 'DISCONNECT')
        bone.select_head = True
        bone.head = (
            bone.head[0] + head_offset[0],
            bone.head[1] + head_offset[1],
            bone.head[2] + head_offset[2])
        bone.select_tail = True
        bone.roll = 0


    def set_object_zero(ob):
        scene = bpy.context.scene

        # Get all the z values of the faces
        vertices = []
        for face in ob.data.polygons:
            face_vertices = face.vertices[:]
            for vertex in face_vertices:
                z = ob.data.vertices[vertex].co[2]
                vertices.append(z)

        # Move the object to the zero point and reset the cursor
        ob.location = (ob.location[0], ob.location[1], -min(vertices))
        scene.cursor.location = (0, 0, 0)

    def select_head(bone):
        bpy.ops.armature.select_all(action='DESELECT')
        bone.select_head = True

    def select_tail(bone):
        bpy.ops.armature.select_all(action='DESELECT')
        bone.select_tail = True

    def create_humaniod_armature(reference_object):
        # Add the armature and all bones
        loc = reference_object.location
        width = reference_object.dimensions[0]
        depth = reference_object.dimensions[1]
        height = reference_object.dimensions[2]
        leg_height = height * 0.39
        head_height = height * 0.1
        torso_height = height * 0.35

        # Spine
        armature = WIZ_OT_base_armature.add_armature((0, 0, height * 0.44), torso_height * 0.1)
        root_bone = armature.data.edit_bones.active
        WIZ_OT_base_armature.add_bone(BONE_NAME.SPINE1.value, (0, 0, torso_height * 0.4))
        shoulder_blade_bone = WIZ_OT_base_armature.add_bone(BONE_NAME.SPINE2.value, (0, 0, torso_height * 0.4))
        WIZ_OT_base_armature.add_bone(BONE_NAME.SPINE3.value, (0, 0, torso_height * 0.2))

        # Head
        WIZ_OT_base_armature.add_bone(BONE_NAME.HEAD.value, (0, 0, head_height))

        # Left arm
        arm_length = width / 2.0
        WIZ_OT_base_armature.select_tail(shoulder_blade_bone)
        left_shoulder_bone = WIZ_OT_base_armature.add_bone(
            BONE_NAME.SHOULDER_L.value, (arm_length * 0.25, 0, 0))

        #WIZ_OT_base_armature.detach_bone(
        #    left_shoulder_bone,
        #    (arm_length * 0.1, 0, -arm_length * 0.06))
        left_upper_arm = WIZ_OT_base_armature.add_bone(BONE_NAME.UPPER_ARM_L.value, (arm_length * 0.26, 0.01, 0))
        WIZ_OT_base_armature.add_bone(BONE_NAME.LOWER_ARM_L.value, (arm_length * 0.26, -0.01, 0))

        # Left hand
        wrist_bone = WIZ_OT_base_armature.add_bone(BONE_NAME.HAND_L.value, (arm_length * 0.08, 0, 0))
        WIZ_OT_base_armature.add_bone(BONE_NAME.FINGER1_L.value, (arm_length * 0.04, 0, 0))
        WIZ_OT_base_armature.add_bone(BONE_NAME.FINGER2_L.value, (arm_length * 0.04, 0, 0))
        WIZ_OT_base_armature.add_bone(BONE_NAME.FINGER3_L.value, (arm_length * 0.04, 0, 0))
        WIZ_OT_base_armature.select_tail(wrist_bone)
        thumb_bone = WIZ_OT_base_armature.add_bone(BONE_NAME.THUMB1_L.value, (-arm_length * 0.005, -depth * 0.15, 0))
        WIZ_OT_base_armature.add_bone(BONE_NAME.THUMB2_L.value, (0, -depth * 0.055, 0))
        #WIZ_OT_base_armature.detach_bone(
        #    thumb_bone,
        #    (-arm_length * 0.005, -depth * 0.1, 0))

        # Left leg
        WIZ_OT_base_armature.select_tail(root_bone)
        WIZ_OT_base_armature.add_bone(
            BONE_NAME.HIP_JOINT_L.value, (width * 0.08, 0, 0))
        left_femer = WIZ_OT_base_armature.add_bone(
            BONE_NAME.UPPER_LEG_L.value, (0, 0.01, -(leg_height * 0.55)))
        WIZ_OT_base_armature.add_bone(BONE_NAME.LOWER_LEG_L.value, (0, 0, -leg_height * 0.55))


        ###left_femer = WIZ_OT_base_armature.add_bone(
        ###    BONE_NAME.UPPER_LEG_L.value, (width * 0.08, 0.01, -(leg_height * 0.5) - (torso_height * 0.2)))
        ###WIZ_OT_base_armature.detach_bone(
        ###    left_femer,
        ###    (width * 0.08, 0.0,  -torso_height * 0.2))
        ###WIZ_OT_base_armature.add_bone(BONE_NAME.LOWER_LEG_L.value, (0, 0, -leg_height * 0.55))

        # Left foot
        left_foot_bone = WIZ_OT_base_armature.add_bone(BONE_NAME.FOOT_L.value, (0, -depth * 0.7, -leg_height * 0.1))
        # Bone Relations remove inherit rotation for the foot.  Prevents unwanted rotations with IK bones.
        left_foot_bone.use_inherit_rotation = False

        # IK Leg Bones
        WIZ_OT_base_armature.select_tail(left_femer)
        left_IK_knee = WIZ_OT_base_armature.add_bone(BONE_NAME.IK_LEG_POLE_L.value, (0, -0.4, 0))
        WIZ_OT_base_armature.detach_bone(
            left_IK_knee,
            (0, -0.3, 0), True)
        WIZ_OT_base_armature.select_head(left_foot_bone)
        left_IK_heel = WIZ_OT_base_armature.add_bone(BONE_NAME.IK_LEG_TARGET_L.value, (0, 0.1, 0))
        WIZ_OT_base_armature.detach_bone(
            left_IK_heel,
            (0, 0, 0), True)
        left_IK_knee.use_deform = False
        left_IK_heel.use_deform = False

        # Constraints
        WIZ_OT_base_armature.add_ik_constraint(armature, BONE_NAME.LOWER_LEG_L.value, BONE_NAME.IK_LEG_TARGET_L.value, BONE_NAME.IK_LEG_POLE_L.value)
        WIZ_OT_base_armature.add_copyrotation_constraint(armature, BONE_NAME.FOOT_L.value, BONE_NAME.IK_LEG_TARGET_L.value)

        WIZ_OT_base_armature.set_pose_mode()
        order = 'ZYX'
        context = bpy.context
        rig_object = context.active_object
        for pb in rig_object.pose.bones:
            pb.rotation_mode = order


    def create_quadruped_armature(reference_object):
        # Add the armature and all bones
        loc = reference_object.location
        width = reference_object.dimensions[0]
        depth = reference_object.dimensions[1]
        height = reference_object.dimensions[2]
        leg_height = height * 0.39
        head_height = height * 0.16
        torso_width = width * 0.5
        torso_height = height * 0.35

        # Spine
        armature = WIZ_OT_base_armature.add_armature((0, width * 0.5, height * 0.68), torso_width * 0.3)
        root_bone = armature.data.edit_bones.active
        WIZ_OT_base_armature.select_tail(root_bone)
        root_bone.tail.y = root_bone.tail.y - width * 0.5
        root_bone.tail.z = root_bone.tail.z - torso_height * 0.3

        WIZ_OT_base_armature.add_bone(BONE_NAME.SPINE1.value, (0, -torso_width * 0.7, -0.01))
        WIZ_OT_base_armature.add_bone(BONE_NAME.SPINE2.value, (0, -torso_width * 0.7, 0))
        spine3_bone = WIZ_OT_base_armature.add_bone(BONE_NAME.SPINE3.value, (0, -torso_width * 0.58, 0.03))
        WIZ_OT_base_armature.add_bone(BONE_NAME.NECK.value, (0, -torso_width * 0.48, 0.035))
        head_bone = WIZ_OT_base_armature.add_bone(BONE_NAME.HEAD.value, (0, -torso_width * 0.7, torso_height * 0.5))

        # Ear
        WIZ_OT_base_armature.select_tail(head_bone)
        ear_bone = WIZ_OT_base_armature.add_bone(BONE_NAME.EAR1_L.value, (depth * 0.07, torso_width * 0.1, 0))
        WIZ_OT_base_armature.detach_bone(
            ear_bone,
            (torso_width * 0.5, torso_width * 0.1, -torso_height * 0.1))
        WIZ_OT_base_armature.add_bone(BONE_NAME.EAR2_L.value, (0, 0, torso_height * 0.03))

        # Tail
        WIZ_OT_base_armature.select_head(root_bone)
        head_tail_bone = WIZ_OT_base_armature.add_bone(BONE_NAME.TAIL1.value, (0, torso_width * 0.51, 0.0038))
        WIZ_OT_base_armature.add_bone(BONE_NAME.TAIL2.value, (0, torso_width * 0.51, 0.0038))
        WIZ_OT_base_armature.add_bone(BONE_NAME.TAIL3.value, (0, torso_width * 0.51, 0.0038))
        mid_tail_bone = WIZ_OT_base_armature.add_bone(BONE_NAME.TAIL4.value, (0, torso_width * 0.51, 0.0038))
        WIZ_OT_base_armature.add_bone(BONE_NAME.TAIL5.value, (0, torso_width * 0.51, 0.0038))
        WIZ_OT_base_armature.add_bone(BONE_NAME.TAIL6.value, (0, torso_width * 0.51, 0.0038))
        WIZ_OT_base_armature.add_bone(BONE_NAME.TAIL7.value, (0, torso_width * 0.51, 0.0038))
        tail_bone = WIZ_OT_base_armature.add_bone(BONE_NAME.TAIL8.value, (0, torso_width * 0.51, 0.0038))
        head_tail_bone.parent = root_bone

        # Left leg
        WIZ_OT_base_armature.select_tail(root_bone)
        left_femer = WIZ_OT_base_armature.add_bone(
            BONE_NAME.UPPER_LEG_L.value, (width * 0.35, width * 0.3, -(leg_height * 0.5) - (torso_height * 0.2)))
        WIZ_OT_base_armature.detach_bone(
            left_femer,
            (width * 0.25, (leg_height * 0.4),  -torso_height * 0.2))
        WIZ_OT_base_armature.add_bone(BONE_NAME.LOWER_LEG_L.value, (width * 0.05, width * 0.38, -leg_height * 0.42))

        # Left foot
        WIZ_OT_base_armature.add_bone(BONE_NAME.FOOT_L.value, (-width * 0.02, width * 0.02, -leg_height * 0.5))
        left_toe_bone = WIZ_OT_base_armature.add_bone(BONE_NAME.TOE_L.value, (width * 0.02, -width * 0.1,0))
        # Bone Relations remove inherit rotation for the foot.  Prevents unwanted rotations with IK bones.
        left_toe_bone.use_inherit_rotation = False


        # Left Front leg
        WIZ_OT_base_armature.select_tail(spine3_bone)
        left_shoulder = WIZ_OT_base_armature.add_bone(
            BONE_NAME.SHOULDER_L.value, (width * 0.35, width * 0.05, -(leg_height * 0.5) - (torso_height * 0.2)))
        WIZ_OT_base_armature.detach_bone(
            left_shoulder,
            (width * 0.25, leg_height * 0.2,  -torso_height * 0.2))
        WIZ_OT_base_armature.add_bone(BONE_NAME.UPPER_ARM_L.value, (0, width * 0.05, -leg_height * 0.35))

        # Left Front foot
        WIZ_OT_base_armature.add_bone(BONE_NAME.LOWER_ARM_L.value, (width * 0.02, -width * 0.04, -leg_height * 0.68))
        left_foot_bone = WIZ_OT_base_armature.add_bone(BONE_NAME.HAND_L.value, (width * 0.05, -width * 0.1,0))
        # Bone Relations remove inherit rotation for the foot.  Prevents unwanted rotations with IK bones.
        left_foot_bone.use_inherit_rotation = False


        # IK Leg Bones
        WIZ_OT_base_armature.select_tail(left_femer)
        left_IK_knee = WIZ_OT_base_armature.add_bone(BONE_NAME.IK_LEG_POLE_L.value, (0, width * 0.7, 0))
        WIZ_OT_base_armature.detach_bone(
            left_IK_knee,
            (0, width * 0.5, 0), True)
        WIZ_OT_base_armature.select_head(left_toe_bone)
        left_IK_heel = WIZ_OT_base_armature.add_bone(BONE_NAME.IK_LEG_TARGET_L.value, (0, width * 0.1, 0))
        WIZ_OT_base_armature.detach_bone(
            left_IK_heel,
            (0, 0, 0), True)
        left_IK_knee.use_deform = False
        left_IK_heel.use_deform = False


        # IK Front Leg Bones
        WIZ_OT_base_armature.select_tail(left_shoulder)
        left_IK_front_knee = WIZ_OT_base_armature.add_bone(BONE_NAME.IK_FRONT_LEG_POLE_L.value, (0, width * 0.7, -height * 0.3))
        WIZ_OT_base_armature.detach_bone(
            left_IK_front_knee,
            (0, width * 0.5, -height * 0.3), True)
        WIZ_OT_base_armature.select_head(left_foot_bone)
        left_front_IK_heel = WIZ_OT_base_armature.add_bone(BONE_NAME.IK_FRONT_LEG_TARGET_L.value, (0, width * 0.1, 0))
        WIZ_OT_base_armature.detach_bone(
            left_front_IK_heel,
            (0, 0, 0), True)
        left_IK_front_knee.use_deform = False
        left_front_IK_heel.use_deform = False


        # IK Tail Bones
        WIZ_OT_base_armature.select_tail(mid_tail_bone)
        tail_IK_base = WIZ_OT_base_armature.add_bone(BONE_NAME.IK_TAIL_POLE.value, (0, 0, -width * 1.1))
        WIZ_OT_base_armature.detach_bone(
            tail_IK_base,
            (0, 0, -width * 0.9), True)
        WIZ_OT_base_armature.select_tail(tail_bone)
        tail_IK_heel = WIZ_OT_base_armature.add_bone(BONE_NAME.IK_TAIL_TARGET.value, (0, width * 0.3, 0))
        WIZ_OT_base_armature.detach_bone(
            tail_IK_heel,
            (0, width * 0.2, 0), True)
        tail_IK_base.use_deform = False
        tail_IK_heel.use_deform = False

        # Constraints
        WIZ_OT_base_armature.add_ik_constraint(armature, BONE_NAME.FOOT_L.value, BONE_NAME.IK_LEG_TARGET_L.value, BONE_NAME.IK_LEG_POLE_L.value, 3)
        WIZ_OT_base_armature.add_copyrotation_constraint(armature, BONE_NAME.TOE_L.value, BONE_NAME.IK_LEG_TARGET_L.value, True, True, False)
        WIZ_OT_base_armature.add_ik_constraint(armature, BONE_NAME.LOWER_ARM_L.value, BONE_NAME.IK_FRONT_LEG_TARGET_L.value, BONE_NAME.IK_FRONT_LEG_POLE_L.value, 2)
        WIZ_OT_base_armature.add_copyrotation_constraint(armature, BONE_NAME.HAND_L.value, BONE_NAME.IK_FRONT_LEG_TARGET_L.value, True, True, False)
        WIZ_OT_base_armature.add_ik_constraint(armature, BONE_NAME.TAIL8.value, BONE_NAME.IK_TAIL_TARGET.value, BONE_NAME.IK_TAIL_POLE.value, 8)

        WIZ_OT_base_armature.set_pose_mode()
        order = 'ZYX'
        context = bpy.context
        rig_object = context.active_object
        for pb in rig_object.pose.bones:
            pb.rotation_mode = order

        # Ensure the tail will automatically bend in a downward motion if you drag the target bone
        pbone = rig_object.pose.bones[BONE_NAME.TAIL8.value]
        pbone.rotation_euler.rotate_axis('X', math.radians(-1))


    def create_generic_armature(reference_object):
        # Add the armature and all bones
        loc = reference_object.location
        width = reference_object.dimensions[0]
        depth = reference_object.dimensions[1]
        height = reference_object.dimensions[2]

        # Spine
        armature = WIZ_OT_base_armature.add_armature((loc.x, loc.y, loc.z + height * 0.5), height * 0.5)
        root_bone = armature.data.edit_bones.active
        WIZ_OT_base_armature.select_tail(root_bone)
        root_bone.tail.z = root_bone.tail.z - height * 0.25

        WIZ_OT_base_armature.set_pose_mode()
        order = 'ZYX'
        context = bpy.context
        rig_object = context.active_object
        for pb in rig_object.pose.bones:
            pb.rotation_mode = order

        reference_object.select_set(True)
        WIZ_OT_base_armature.set_object_mode()
        WIZ_OT_base_armature.assign_arm_to_mesh(armature)

        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME', center='MEDIAN')

        bpy.context.active_object["godot_object_type"] = OBJECT_TYPE.GENERIC_ARMATURE.name


    def create_door_armature(reference_object):
        # Add the armature and all bones
        loc = reference_object.location
        width = reference_object.dimensions[0]
        depth = reference_object.dimensions[1]
        height = reference_object.dimensions[2]

        # Spine
        armature = WIZ_OT_base_armature.add_armature((loc.x - width * 0.5, loc.y, loc.z + height * 0.5), width * 0.5)
        root_bone = armature.data.edit_bones.active
        WIZ_OT_base_armature.select_tail(root_bone)
        root_bone.tail.x = root_bone.tail.x + width * 0.5
        root_bone.tail.z = root_bone.tail.z - width * 0.25

        WIZ_OT_base_armature.set_pose_mode()
        order = 'ZYX'
        context = bpy.context
        rig_object = context.active_object
        for pb in rig_object.pose.bones:
            pb.rotation_mode = order

        reference_object.select_set(True)
        WIZ_OT_base_armature.set_object_mode()
        WIZ_OT_base_armature.assign_arm_to_mesh(armature)

        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME', center='MEDIAN')

        bpy.context.active_object["godot_object_type"] = OBJECT_TYPE.DOOR.name


    def create_double_door_armature(reference_object):
        # Add the armature and all bones
        loc = reference_object.location
        width = reference_object.dimensions[0]
        depth = reference_object.dimensions[1]
        height = reference_object.dimensions[2]

        # Left Door Bone
        armature = WIZ_OT_base_armature.add_armature((loc.x - width * 0.5, loc.y, loc.z + height * 0.5), width * 0.25)
        left_door_bone = armature.data.edit_bones.active
        WIZ_OT_base_armature.select_tail(left_door_bone)
        left_door_bone.tail.x = left_door_bone.tail.x + width * 0.25
        left_door_bone.tail.z = left_door_bone.tail.z - width * 0.25

        # Right Door Bone
        right_door_bone = WIZ_OT_base_armature.add_bone("root.right", (width * 0.5, 0, 0))
        WIZ_OT_base_armature.detach_bone(
            right_door_bone,
            (width * 0.75, 0, 0), True)

        WIZ_OT_base_armature.set_pose_mode()
        order = 'ZYX'
        context = bpy.context
        rig_object = context.active_object
        for pb in rig_object.pose.bones:
            pb.rotation_mode = order

        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME', center='MEDIAN')

        reference_object.select_set(True)
        WIZ_OT_base_armature.set_object_mode()
        WIZ_OT_base_armature.assign_arm_to_mesh(armature)

        bpy.context.active_object["godot_object_type"] = OBJECT_TYPE.DOOR.name


    def add_ik_constraint(armature, source_bone_name, target_bone_name, pole_bone_name, chain_count = 2):
        WIZ_OT_base_armature.set_pose_mode()
        pose_bone_lowerleg = armature.pose.bones.get(source_bone_name)
        crc = pose_bone_lowerleg.constraints.new('IK')
        crc.target = armature
        crc.subtarget = target_bone_name
        crc.pole_target = armature
        crc.pole_subtarget = pole_bone_name
        crc.pole_angle = math.radians(90)
        crc.chain_count = chain_count


    def add_copyrotation_constraint(
        armature,
        source_bone_name,
        target_bone_name,
        invert_rotation_x = False, invert_rotation_y = False, invert_rotation_z = True):
        pose_bone_foot = armature.pose.bones.get(source_bone_name)
        constraint = pose_bone_foot.constraints.new('COPY_ROTATION')
        constraint.target = armature
        constraint.subtarget = target_bone_name
        constraint.owner_space = 'LOCAL'
        constraint.target_space = 'LOCAL'
        constraint.invert_x = invert_rotation_x
        constraint.invert_y = invert_rotation_y
        constraint.invert_z = invert_rotation_z

    def add_childof_constraint(armature, mesh, bone_name):
        WIZ_OT_base_armature.set_pose_mode()

        # For all childof constraints set the influence to 0 if they are not the selected bone which we instead set to 1.0
        for constraint in mesh.constraints:
            if constraint.type == "CHILD_OF":
                constraint.influence = 1.0 if constraint.subtarget == bone_name else 0

        # If the constraint doesn't already exist add it
        constraints = [constraint for constraint in mesh.constraints if constraint.type == "CHILD_OF" and  constraint.subtarget == bone_name]
        if not constraints:
            constraint = mesh.constraints.new('CHILD_OF')
            constraint.target = armature
            constraint.subtarget = bone_name
            constraint.owner_space = 'WORLD'
            constraint.target_space = 'WORLD'
            constraint.influence = 1.0

def add_rigify_arm(type: str):
        try:
            if type == "human":
                bpy.ops.object.armature_human_metarig_add()
            if type == "basic_human":
                bpy.ops.object.armature_basic_human_metarig_add()
            if type == "quadruped":
                bpy.ops.object.armature_basic_quadruped_metarig_add()
            if type == "cat":
                bpy.ops.object.armature_cat_metarig_add()
            if type == "bird":
                bpy.ops.object.armature_bird_metarig_add()
            if type == "horse":
                bpy.ops.object.armature_horse_metarig_add()
            if type == "shark":
                bpy.ops.object.armature_shark_metarig_add()
            if type == "wolf":
                bpy.ops.object.armature_wolf_metarig_add()

            bpy.context.active_object["godot_object_type"] = OBJECT_TYPE.ARMATURE.name
            WIZ_OT_base_armature.set_pose_mode()
            bpy.context.active_object.show_in_front = True

        except AttributeError:
            info("Please install the rigify plugin first")
        return {'FINISHED'}


class WIZ_OT_add_rigify_human(bpy.types.Operator):
    bl_label = "Simple operator"
    bl_idname = "view3d.add_rigify_human"
    bl_description = "Add a human armature to the selected object"
    def execute(caller, context):
        return add_rigify_arm("human")

class WIZ_OT_add_rigify_basic_human(bpy.types.Operator):
    bl_label = "Simple operator"
    bl_idname = "view3d.add_rigify_basic_human"
    bl_description = "Add a basic human armature to the selected object"
    def execute(caller, context):
        return add_rigify_arm("basic_human")

class WIZ_OT_add_rigify_basic_quadruped(bpy.types.Operator):
    bl_label = "Simple operator"
    bl_idname = "view3d.add_rigify_basic_quadruped"
    bl_description = "Add a basic quadruped armature to the selected object"
    def execute(caller, context):
        return add_rigify_arm("quadruped")

class WIZ_OT_add_rigify_bird(bpy.types.Operator):
    bl_label = "Simple operator"
    bl_idname = "view3d.add_rigify_bird"
    bl_description = "Add a bird armature to the selected object"
    def execute(caller, context):
        return add_rigify_arm("bird")

class WIZ_OT_add_rigify_cat(bpy.types.Operator):
    bl_label = "Simple operator"
    bl_idname = "view3d.add_rigify_cat"
    bl_description = "Add a cat armature to the selected object"
    def execute(caller, context):
        return add_rigify_arm("cat")

class WIZ_OT_add_rigify_horse(bpy.types.Operator):
    bl_label = "Simple operator"
    bl_idname = "view3d.add_rigify_horse"
    bl_description = "Add a horse armature to the selected object"
    def execute(caller, context):
        return add_rigify_arm("horse")

class WIZ_OT_add_rigify_shark(bpy.types.Operator):
    bl_label = "Simple operator"
    bl_idname = "view3d.add_rigify_shark"
    bl_description = "Add a shark armature to the selected object"
    def execute(caller, context):
        return add_rigify_arm("shark")

class WIZ_OT_add_rigify_wolf(bpy.types.Operator):
    bl_label = "Simple operator"
    bl_idname = "view3d.add_rigify_wolf"
    bl_description = "Add a wolf armature to the selected object"
    def execute(caller, context):
        return add_rigify_arm("wolf")

class WIZ_OT_add_armature_human(WIZ_OT_base_armature):
    bl_idname = "view3d.add_armature_human"
    bl_description = "Add a human armature to the selected object"

    def execute(caller, context):
        ob = bpy.context.active_object
        selected_objects = bpy.context.selected_objects
        if not selected_objects or len(selected_objects) != 1 or not ob:
            info("Please select only one object first")
            return {'FINISHED'}

        WIZ_OT_base_armature.set_edit_mode()

        # Ensure the selected object has a zero point at the bottom
        WIZ_OT_base_armature.set_object_zero(ob)

        WIZ_OT_base_armature.set_object_mode()

        WIZ_OT_base_armature.create_humaniod_armature(ob)

        WIZ_OT_base_armature.set_edit_mode()

        return {'FINISHED'}



class WIZ_OT_add_armature_quadruped(WIZ_OT_base_armature):
    bl_idname = "view3d.add_armature_quadruped"
    bl_description = "Add an animal armature to the selected object"

    def execute(caller, context):
        ob = bpy.context.active_object
        selected_objects = bpy.context.selected_objects
        if not selected_objects or len(selected_objects) != 1 or not ob:
            info("Please select only one object first")
            return {'FINISHED'}

        WIZ_OT_base_armature.set_edit_mode()

        # Ensure the selected object has a zero point at the bottom
        WIZ_OT_base_armature.set_object_zero(ob)

        WIZ_OT_base_armature.set_object_mode()

        WIZ_OT_base_armature.create_quadruped_armature(ob)

        WIZ_OT_base_armature.set_edit_mode()

        return {'FINISHED'}

class WIZ_OT_add_armature_generic(WIZ_OT_base_armature):
    bl_idname = "view3d.add_armature_generic"
    bl_description = "Add a generic armature to the selected object"

    def execute(caller, context):
        ob = bpy.context.active_object
        selected_objects = bpy.context.selected_objects
        if not selected_objects or len(selected_objects) != 1 or not ob:
            info("Please select only one object first")
            return {'FINISHED'}

        WIZ_OT_base_armature.set_edit_mode()

        # Ensure the selected object has a zero point at the bottom
       # WIZ_OT_base_armature.set_object_zero(ob)

        WIZ_OT_base_armature.set_object_mode()

        WIZ_OT_base_armature.create_generic_armature(ob)

        #bpy.context.object.data.display_type = "STICK"

        return {'FINISHED'}

class WIZ_OT_add_armature_door(WIZ_OT_base_armature):
    bl_idname = "view3d.add_armature_door"
    bl_description = "Add a door armature to the selected object"

    def execute(caller, context):
        ob = bpy.context.active_object
        selected_objects = bpy.context.selected_objects
        if not selected_objects or len(selected_objects) != 1 or not ob:
            info("Please select only one object first")
            return {'FINISHED'}

        WIZ_OT_base_armature.set_edit_mode()

        # Ensure the selected object has a zero point at the bottom
       # WIZ_OT_base_armature.set_object_zero(ob)

        WIZ_OT_base_armature.set_object_mode()

        WIZ_OT_base_armature.create_door_armature(ob)

        #bpy.context.object.data.display_type = "STICK"

        return {'FINISHED'}


class WIZ_OT_add_armature_double_door(WIZ_OT_base_armature):
    bl_idname = "view3d.add_armature_double_door"
    bl_description = "Add a double door armature to the selected object"

    def execute(caller, context):
        ob = bpy.context.active_object
        selected_objects = bpy.context.selected_objects
        if not selected_objects or len(selected_objects) != 1 or not ob:
            info("Please select only one object first")
            return {'FINISHED'}

        WIZ_OT_base_armature.set_edit_mode()

        # Ensure the selected object has a zero point at the bottom
       # WIZ_OT_base_armature.set_object_zero(ob)

        WIZ_OT_base_armature.set_object_mode()

        WIZ_OT_base_armature.create_double_door_armature(ob)

        #bpy.context.object.data.display_type = "STICK"

        return {'FINISHED'}


class WIZ_OT_symeterize_armature(WIZ_OT_base_armature):
    bl_idname = "view3d.symeterize_armature"
    bl_description = "Make an armature symetrical"

    def execute(caller, context):
        ob = bpy.context.active_object
        if not ob or ob.type != "ARMATURE":
            info("Please select an armature")
            return {'FINISHED'}

        WIZ_OT_base_armature.set_edit_mode()

        bpy.ops.armature.select_all(action='SELECT')
        bpy.ops.armature.symmetrize(direction='NEGATIVE_X')

        WIZ_OT_base_armature.set_object_mode()

        return {'FINISHED'}


class WIZ_OT_parent_armature(WIZ_OT_base_armature):
    bl_idname = "view3d.parent_armature"
    bl_description = "Make an armature the parent of a mesh"

    def execute(caller, context):
        selected_objects = bpy.context.selected_objects
        if not selected_objects or len(selected_objects) <= 1:
            info("Please select an armature and a mesh")
            return {'FINISHED'}

        # Find the armature in the selected objects.  Deselect and reselect it so it is the last thing
        # selected before the assignment
        arm = None
        for ob in selected_objects:
            if ob.type == "ARMATURE":
                arm = ob

        if not arm:
            info("Please select one armature and a mesh")
            return {'FINISHED'}

        WIZ_OT_base_armature.assign_arm_to_mesh(arm)

        WIZ_OT_base_armature.set_object_mode()

        return {'FINISHED'}
