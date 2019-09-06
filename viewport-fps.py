#    Viewport FPS is a blender add-on that calculates minimum, maximum
#    and average viewport FPS.
#    Copyright (C) 2019 Scott Winkelmann
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import bpy
import time

bl_info = {
    "name":        "Viewport FPS",
    "author":      "Scott Winkelmann <scottlandart@gmail.com>",
    "version":     (1, 0, 1),
    "blender":     (2, 80, 0),
    "location":    "Properties Panel > Active Tool and Workspace settings",
    "description": "This add-on calculates the minimum, maximum and average FPS of the viewport",
    "warning":     "",
    "wiki_url":    "https://github.com/ScottishCyclops/viewport-fps",
    "tracker_url": "https://github.com/ScottishCyclops/viewport-fps/issues",
    "category":    "Development"
}

# constant
skiped_frames = 5

# global variables
minimum_fps = None
maximum_fps = None
average_fps = None
total_fps = 0.0
passed_frames = 0.0
last_time = time.time()
running_test = False


def start_test():
    """
    Initialize the test data, set the running flag and start the animation
    :return: nothing
    """
    global minimum_fps, maximum_fps, average_fps, total_fps, passed_frames, last_time, running_test

    # reset
    minimum_fps = None
    maximum_fps = None
    average_fps = None
    total_fps = 0.0
    passed_frames = 0.0
    last_time = time.time()

    # set flag
    running_test = True
    # start the animation
    bpy.ops.screen.animation_play()


def stop_test():
    """
    Set the running flag and stop the animation
    :return: nothing
    """
    global running_test

    running_test = False

    bpy.ops.screen.animation_cancel()


def wf_update_handler(scene):
    """
    Updates the minimum, maximum and average FPS if a test is running
    Stop the test if it reached its end
    :param scene: the scene to operate on
    :return: nothing
    """

    if not running_test:
        return

    global last_time, minimum_fps, maximum_fps, average_fps, total_fps, passed_frames

    # check if test has reached the end
    if passed_frames >= scene.wf_test_length:
        stop_test()
        return

    # increase the number of frames
    passed_frames += 1.0

    # time calculations
    current_time = time.time()
    frame_time = current_time - last_time
    last_time = current_time

    # skip a few frames, because the interval is not accurate in the beginning
    if passed_frames <= skiped_frames:
        return

    # compute instant frames per second
    fps = 1.0 / frame_time

    # compute average fps
    total_fps += fps
    average_fps = total_fps / (passed_frames - skiped_frames)

    # compute minimum and maximum
    if minimum_fps is None or fps < minimum_fps:
        minimum_fps = fps
    if maximum_fps is None or fps > maximum_fps:
        maximum_fps = fps


class WfRunTest(bpy.types.Operator):
    """Run an FPS test"""

    bl_label = "Run FPS test"
    bl_idname = "wf.run_test"
    bl_options = {"REGISTER"}

    def execute(self, context):
        start_test()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class WfCancelTest(bpy.types.Operator):
    """Cancel the current FPS test"""

    bl_label = "Cancel FPS test"
    bl_idname = "wf.cancel_test"
    bl_options = {"REGISTER"}

    def execute(self, context):
        stop_test()
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class WfPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""

    bl_label = "Viewport FPS"
    bl_idname = "VIEW_3D_PT_wf"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"

    def draw(self, context):
        flow = self.layout.column()

        length = 1.0 if context.scene.wf_test_length == 0 else float(
            context.scene.wf_test_length)

        test_progress = passed_frames / length * 100.0

        row1 = flow.column()

        if running_test:
            row1.label(text="Progress: {0:.1f}%".format(test_progress))
        else:
            row1.prop(context.scene, "wf_test_length",
                      text="Test frame length")

        row1.operator("wf.cancel_test" if running_test else "wf.run_test")

        box = row1.box()
        row = box.row()

        col1 = row.column()
        col1.label(text="Minimum")
        col1.label(text="Maximum")
        col1.label(text="Average")

        col2 = row.column()
        col2.label(text="{0:.2f} FPS".format(
            0 if minimum_fps is None else minimum_fps))
        col2.label(text="{0:.2f} FPS".format(
            0 if maximum_fps is None else maximum_fps))
        col2.label(text="{0:.2f} FPS".format(
            0 if average_fps is None else average_fps))


def add_props():
    """
    Method responsible for adding properties
    :return: nothing
    """
    bpy.types.Scene.wf_test_length = bpy.props.IntProperty(
        name="wf_test_length",
        description="Number of frames to run for a test",
        default=500,
        min=skiped_frames,
        options=set())


def remove_props():
    """
    Method responsible for removing properties
    :return: nothing
    """
    del bpy.types.Scene.wf_test_length


def add_handlers():
    """
    Method responsible for adding the handlers for the wf_update_handler method
    :return: nothing
    """
    bpy.app.handlers.persistent(wf_update_handler)
    bpy.app.handlers.frame_change_post.append(wf_update_handler)


def remove_handlers():
    """
    Method responsible for removing the handlers for the wf_update_handler method
    :return: nothing
    """
    bpy.app.handlers.frame_change_post.remove(wf_update_handler)


def register():
    """
    Method called by Blender when enabling the add-on
    :return: nothing
    """
    add_props()
    bpy.utils.register_class(WfRunTest)
    bpy.utils.register_class(WfCancelTest)
    bpy.utils.register_class(WfPanel)
    add_handlers()


def unregister():
    """
    Method called by Blender when disabling or removing the add-on
    :return: nothing
    """
    remove_handlers()
    bpy.utils.unregister_class(WfPanel)
    bpy.utils.unregister_class(WfCancelTest)
    bpy.utils.unregister_class(WfRunTest)
    remove_props()


# if the script is run directly, register it
if __name__ == "__main__":
    register()
