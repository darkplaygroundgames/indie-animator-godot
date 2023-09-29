import os
import bpy
from . utils import *


def import_fbx(animation_file: str) -> bool:
    try:
        bpy.ops.import_scene.fbx(
            filepath=animation_file,
            use_anim=True,
            automatic_bone_orientation=False,
            bake_space_transform=True,
            #ignore_leaf_bones=True,
            #force_connect_children=False,
            ui_tab='ARMATURE')
        return True
    except Exception as err:
        info(f"Failed to load invalid fbx file {animation_file} (Error: {str(err)}")

    return False

def import_bvh(animation_file: str) -> bool:
    try:
        bpy.ops.import_anim.bvh(
            filepath=animation_file,
            target='ARMATURE',
            #use_fps_scale=True,
            #update_scene_fps=True,
            #update_scene_duration=True,
            #use_cyclic=True,
            rotate_mode='QUATERNION',
            #axis_forward='Y',
            #axis_up='Z'
        )
        return True
    except Exception as err:
        info(f"Failed to load invalid fbx file {animation_file} (Error: {str(err)}")

    return False


def verify_armatures(src_arm, dst_arm) -> bool:
    """
    Check the bone names of both armatures to ensure they match.  If the
    animations are from a different armature type (eg. Rigify vs Mixamo)
    then the bone names won't match and the animations won't work properly.
    """
    # Get the list of source bone names
    src_bone_names =  sorted(list(set([bone.name for bone in src_arm.pose.bones])))
    dst_bone_names =  sorted(list(set([bone.name for bone in dst_arm.pose.bones])))

    for bone_name in src_bone_names:
        if bone_name not in dst_bone_names:
            return False

    return True


def remove_armature(arm) -> bool:
    """
    Take the armature, find any other meshes that may be included
    and remove them all
    """
    for ob in bpy.data.objects:
        if ob.parent == arm:
            bpy.data.objects.remove(ob)
    bpy.data.objects.remove(arm)

def edit_animation(caller, context):
        scene = bpy.context.scene
        dst_arm = bpy.context.active_object
        if not dst_arm or dst_arm.type != "ARMATURE":
            info("Please select a destination armature")
            return {'FINISHED'}

        if not scene.edit_animation_file:
            info("Please select an animation file")
            return {'FINISHED'}

        fbx = scene.edit_animation_file.endswith(".fbx")
        bvh = scene.edit_animation_file.endswith(".bvh")
        if not (fbx or bvh):
            info("Please select an fbx or bvh animation file")
            return {'FINISHED'}

        file_path = bpy.path.abspath(scene.edit_animation_file)
        name = os.path.basename(file_path).rsplit(".", 1)[0].lower()

        # Import the armature from the animation file
        if fbx and not import_fbx(file_path):
            return {'FINISHED'}
        elif bvh and not import_bvh(file_path):
            return {'FINISHED'}

        # Select the new armature
        src_arm = bpy.context.active_object

        # Ensure the bone names of the src and dst match.  Otherwise there will
        # be weird issues where the animations don't work.  For example, we don't
        # want to apply mixamo animations to a rigify armature or vice versa
        if verify_armatures(src_arm, dst_arm):
            # Update the name of the new animation
            src_arm.animation_data.action.name = name

            # Load the animation in a way that is editable in the animation tab
            dst_arm.animation_data.action = bpy.data.actions[name]
        else:
            info("Failed to import animation.  The armature types and bone names must match")

        # Select the original armature again
        bpy.data.objects.remove(src_arm)
        bpy.ops.object.select_all(action='DESELECT')
        dst_arm.select_set(True)
        bpy.context.view_layer.objects.active = dst_arm

        return {'FINISHED'}


def import_animations(caller, context):
    scene = bpy.context.scene
    dst_arm = bpy.context.active_object
    if not dst_arm or dst_arm.type != "ARMATURE":
        info("Please select a destination armature")
        return {'FINISHED'}

    if not scene.animation_file:
        info("Please select an animation file")
        return {'FINISHED'}

    fbx = scene.animation_file.endswith(".fbx")
    bvh = scene.animation_file.endswith(".bvh")
    if not (fbx or bvh):
        info("Please select an fbx or bvh animation file")
        return {'FINISHED'}

    file_path = bpy.path.abspath(scene.animation_file)
    name = os.path.basename(file_path).rsplit(".", 1)[0].lower()

    # Get the list of animations that already exist in the destination
    animations = []
    if dst_arm.animation_data:
        for track in dst_arm.animation_data.nla_tracks:
            for animation in track.strips:
                animations.append(animation.name)

    if name in animations:
        info("An animation with that name already exists")
        return {'FINISHED'}

    # Import the armature from the animation file
    if fbx and not import_fbx(file_path):
        return {'FINISHED'}
    elif bvh and not import_bvh(file_path):
        return {'FINISHED'}

    # Select the new armature
    src_arm = bpy.context.active_object

    # Ensure the bone names of the src and dst match.  Otherwise there will
    # be weird issues where the animations don't work.  For example, we don't
    # want to apply mixamo animations to a rigify armature or vice versa
    if verify_armatures(src_arm, dst_arm):
        # Update the name of the new animation
        src_arm.animation_data.action.name = name

        # If no animation data exists create it
        dst_arm.select_set(True)
        if not dst_arm.animation_data:
            dst_arm.animation_data_create()

        # Create a new tack and animation strip
        action = bpy.data.actions[name]
        track = dst_arm.animation_data.nla_tracks.new()
        track.name = f"track_{name}"
        track.strips.new(name, 1, action)
    else:
        info("Failed to import animation.  The armature types and bone names must match")

    # Select the original armature again
    remove_armature(src_arm)
    bpy.ops.object.select_all(action='DESELECT')
    dst_arm.select_set(True)
    bpy.context.view_layer.objects.active = dst_arm

    return {'FINISHED'}


class WIZ_OT_play_animation(bpy.types.Operator):
    bl_label = "Simple operator"
    bl_idname = "view3d.play_animation"
    bl_description = "Play or stop the latest animation"

    def execute(caller, context):
        bpy.ops.screen.animation_play()
        return {'FINISHED'}
