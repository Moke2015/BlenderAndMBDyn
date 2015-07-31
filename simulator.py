# --------------------------------------------------------------------------
# BlenderAndMBDyn
# Copyright (C) 2015 G. Douglas Baldwin - http://www.baldwintechnology.com
# --------------------------------------------------------------------------
# ***** BEGIN GPL LICENSE BLOCK *****
#
#    This file is part of BlenderAndMBDyn.
#
#    BlenderAndMBDyn is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    BlenderAndMBDyn is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with BlenderAndMBDyn.  If not, see <http://www.gnu.org/licenses/>.
#
# ***** END GPL LICENCE BLOCK *****
# -------------------------------------------------------------------------- 

if "bpy" in locals():
    import imp
    imp.reload(bpy)
    imp.reload(Operator)
    imp.reload(Entity)
else:
    from .base import bpy, BPY, root_dot, database, Operator, Entity, Bundle, enum_general_data, enum_method, enum_nonlinear_solver, enum_eigenanalysis, enum_abort_after, enum_linear_solver, enum_dummy_steps, enum_output_data, enum_real_time, enum_assembly, enum_job_control, enum_default_output, enum_default_aerodynamic_output, enum_default_beam_output
    from .common import FORMAT
    from bpy_extras.io_utils import ExportHelper
    from mathutils import Matrix
    import subprocess
    from tempfile import TemporaryFile
    from time import sleep, clock
    import os

types = ["Initial value"]

tree = ["Add Simulator", types]

klasses = dict()

class Base(Operator):
    bl_label = "Simulators"
    @classmethod
    def make_list(self, ListItem):
        bpy.types.Scene.simulator_uilist = bpy.props.CollectionProperty(type = ListItem)
        def update(self, context):
            if database.simulator and self.simulator_index < len(database.simulator):
                exec("bpy.ops." + root_dot + "save('INVOKE_DEFAULT')")
        bpy.types.Scene.simulator_index = bpy.props.IntProperty(default=-1, update=update)
    @classmethod
    def delete_list(self):
        del bpy.types.Scene.simulator_uilist
        del bpy.types.Scene.simulator_index
    @classmethod
    def get_uilist(self, context):
        return context.scene.simulator_index, context.scene.simulator_uilist
    def set_index(self, context, value):
        context.scene.simulator_index = value
    def prereqs(self, context):
        pass
    def draw_panel_post(self, context, layout):
        if context.scene.dirty_simulator:
            layout.label("Choose a simulator")
        else:
            layout.operator(root_dot + "simulate")
            if context.scene.clean_log:
                layout.operator(root_dot + "animate")

for t in types:
    class Tester(Base):
        bl_label = t
        @classmethod
        def poll(cls, context):
            return False
        def assign(self, context):
            self.entity = database.simulator[context.scene.simulator_index]
        def store(self, context):
            self.entity = database.simulator[self.index]
        def create_entity(self):
            return Entity(self.name)
    klasses[t] = Tester

class InitialValue(Entity):
    def write_input_file(self, context, directory):
        with open(os.path.join(directory, context.scene.name + ".mbd"), "w") as f:
            database.write_indexes(f)
            f.write(
                "begin: data" +
                ";\n\tproblem: initial value" +
                ";\nend: data" +
                ";\n\nbegin: initial value" +
                ";\n\tinitial time: " + FORMAT(self.initial_time) +
                ";\n\tfinal time: " + ("forever" if self.forever else FORMAT(self.final_time)) +
                ";\n")
            problem_count = len([v for v in [True, self.set_method, self.set_nonlinear_solver,
                self.set_eigenanalysis, self.set_abort_after, self.set_linear_solver,
                self.set_dummy_steps, True, self.set_real_time] if v])
            for link in self.links[:problem_count]:
                link.write(f)
            f.write("end: initial value;\n" +
                "\nbegin: control data;\n")
            for link in self.links[problem_count:]:
                link.write(f)
            database.write_control(f, context)
            f.write("end: control data;\n")
            database.write(f)

class InitialValueOperator(Base):
    bl_label = "Initial value"
    executable_path = bpy.props.StringProperty(name="MBDyn path", description="Path to the MBDyn executable")
    initial_time = bpy.props.FloatProperty(name="Initial time", description="When to start simulation (s)", default=0.0, min=0.0, precision=6)
    forever = bpy.props.BoolProperty(name="Forever")
    final_time = bpy.props.FloatProperty(name="Final time", description="When to end simulation (s)", default=10.0, min=0.0, precision=6)
    general_data_name = bpy.props.EnumProperty(items=enum_general_data, name="General data")
    general_data_edit = bpy.props.BoolProperty(name="")
    set_method = bpy.props.BoolProperty(name="Set method")
    method_name = bpy.props.EnumProperty(items=enum_method, name="Method")
    method_edit = bpy.props.BoolProperty(name="")
    set_nonlinear_solver = bpy.props.BoolProperty(name="Set nonlinear solver")
    nonlinear_solver_name = bpy.props.EnumProperty(items=enum_nonlinear_solver, name="Nonlinear solver")
    nonlinear_solver_edit = bpy.props.BoolProperty(name="")
    set_eigenanalysis = bpy.props.BoolProperty(name="Set eigenanalysis")
    eigenanalysis_name = bpy.props.EnumProperty(items=enum_eigenanalysis, name="Eigenanalysis")
    eigenanalysis_edit = bpy.props.BoolProperty(name="")
    set_abort_after = bpy.props.BoolProperty(name="Set abort after")
    abort_after_name = bpy.props.EnumProperty(items=enum_abort_after, name="Abort after")
    abort_after_edit = bpy.props.BoolProperty(name="")
    set_linear_solver = bpy.props.BoolProperty(name="Set linear solver")
    linear_solver_name = bpy.props.EnumProperty(items=enum_linear_solver, name="Linear solver")
    linear_solver_edit = bpy.props.BoolProperty(name="")
    set_dummy_steps = bpy.props.BoolProperty(name="Set dummy steps")
    dummy_steps_name = bpy.props.EnumProperty(items=enum_dummy_steps, name="Dummy steps")
    dummy_steps_edit = bpy.props.BoolProperty(name="")
    output_data_name = bpy.props.EnumProperty(items=enum_output_data, name="Output data")
    output_data_edit = bpy.props.BoolProperty(name="")
    set_real_time = bpy.props.BoolProperty(name="Set real time")
    real_time_name = bpy.props.EnumProperty(items=enum_real_time, name="Real time")
    real_time_edit = bpy.props.BoolProperty(name="")
    set_assembly = bpy.props.BoolProperty(name="Set assembly")
    assembly_name = bpy.props.EnumProperty(items=enum_assembly, name="Assembly")
    assembly_edit = bpy.props.BoolProperty(name="")
    job_control_name = bpy.props.EnumProperty(items=enum_job_control, name="Job control")
    job_control_edit = bpy.props.BoolProperty(name="")
    set_default_output = bpy.props.BoolProperty(name="Set default output", default=True)
    default_output_name = bpy.props.EnumProperty(items=enum_default_output, name="Default output")
    default_output_edit = bpy.props.BoolProperty(name="")
    set_default_aerodynamic_output = bpy.props.BoolProperty(name="Set default aerodynamic output")
    default_aerodynamic_output_name = bpy.props.EnumProperty(items=enum_default_aerodynamic_output, name="Default aerodynamic output")
    default_aerodynamic_output_edit = bpy.props.BoolProperty(name="")
    set_default_beam_output = bpy.props.BoolProperty(name="Set beam default output")
    default_beam_output_name = bpy.props.EnumProperty(items=enum_default_beam_output, name="Default beam output")
    default_beam_output_edit = bpy.props.BoolProperty(name="")
    @classmethod
    def poll(self, context):
        return True
    def prereqs(self, context):
        self.drive_exists(context)
        self.meter_drive_exists(context)
        self.general_data_exists(context)
        self.method_exists(context)
        self.nonlinear_solver_exists(context)
        self.eigenanalysis_exists(context)
        self.abort_after_exists(context)
        self.linear_solver_exists(context)
        self.dummy_steps_exists(context)
        self.output_data_exists(context)
        self.real_time_exists(context)
        self.assembly_exists(context)
        self.job_control_exists(context)
        self.default_output_exists(context)
        self.default_aerodynamic_output_exists(context)
        self.default_beam_output_exists(context)
        self.executable_path = BPY.executable_path
    def assign(self, context):
        self.entity = database.simulator[context.scene.simulator_index]
        self.executable_path = BPY.executable_path
        self.initial_time = self.entity.initial_time
        self.forever = self.entity.forever
        self.final_time = self.entity.final_time
        link = iter(self.entity.links)
        self.general_data_name = next(link).name
        self.set_method = self.entity.set_method
        if self.set_method:
            self.method_name = next(link).name
        self.set_nonlinear_solver = self.entity.set_nonlinear_solver
        if self.set_nonlinear_solver:
            self.nonlinear_solver_name = next(link).name
        self.set_eigenanalysis = self.entity.set_eigenanalysis
        if self.set_eigenanalysis:
            self.eigenanalysis_name = next(link).name
        self.set_abort_after = self.entity.set_abort_after
        if self.set_abort_after:
            self.abort_after_name = next(link).name
        self.set_linear_solver = self.entity.set_linear_solver
        if self.set_linear_solver:
            self.linear_solver_name = next(link).name
        self.set_dummy_steps = self.entity.set_dummy_steps
        if self.set_dummy_steps:
            self.dummy_steps_name = next(link).name
        self.output_data_name = next(link).name
        self.set_real_time = self.entity.set_real_time
        if self.set_real_time:
            self.real_time_name = next(link).name
        self.set_assembly = self.entity.set_assembly
        if self.set_assembly:
            self.assembly_name = next(link).name
        self.job_control_name = next(link).name
        self.set_default_output = self.entity.set_default_output
        if self.set_default_output:
            self.default_output_name = next(link).name
        self.set_default_aerodynamic_output = self.entity.set_default_aerodynamic_output
        if self.set_default_aerodynamic_output:
            self.default_aerodynamic_output_name = next(link).name
        self.set_default_beam_output = self.entity.set_default_beam_output
        if self.set_default_beam_output:
            self.default_beam_output_name = next(link).name
    def store(self, context):
        self.entity = database.simulator[self.index]
        BPY.executable_path = self.executable_path
        self.entity.executable_path = self.executable_path
        self.entity.initial_time = self.initial_time
        self.entity.forever = self.forever
        self.entity.final_time = self.final_time
        self.entity.set_method = self.set_method
        self.entity.set_nonlinear_solver = self.set_nonlinear_solver
        self.entity.set_eigenanalysis = self.set_eigenanalysis
        self.entity.set_abort_after = self.set_abort_after
        self.entity.set_linear_solver = self.set_linear_solver
        self.entity.set_dummy_steps = self.set_dummy_steps
        self.entity.set_real_time = self.set_real_time
        self.entity.set_assembly = self.set_assembly
        self.entity.set_default_output = self.set_default_output
        self.entity.set_default_aerodynamic_output = self.set_default_aerodynamic_output
        self.entity.set_default_beam_output = self.set_default_beam_output
        self.entity.unlink_all()
        self.link_definition(context, self.general_data_name, self.general_data_edit)
        if self.set_method:
            self.link_definition(context, self.method_name, self.method_edit)
        if self.set_nonlinear_solver:
            self.link_definition(context, self.nonlinear_solver_name, self.nonlinear_solver_edit)
        if self.set_eigenanalysis:
            self.link_definition(context, self.eigenanalysis_name, self.eigenanalysis_edit)
        if self.set_abort_after:
            self.link_definition(context, self.abort_after_name, self.abort_after_edit)
        if self.set_linear_solver:
            self.link_definition(context, self.linear_solver_name, self.linear_solver_edit)
        if self.set_dummy_steps:
            self.link_definition(context, self.dummy_steps_name, self.dummy_steps_edit)
        self.link_definition(context, self.output_data_name, self.output_data_edit)
        if self.set_real_time:
            self.link_definition(context, self.real_time_name, self.real_time_edit)
        if self.set_assembly:
            self.link_definition(context, self.assembly_name, self.assembly_edit)
        self.link_definition(context, self.job_control_name, self.job_control_edit)
        if self.set_default_output:
            self.link_definition(context, self.default_output_name, self.default_output_edit)
        if self.set_default_aerodynamic_output:
            self.link_definition(context, self.default_aerodynamic_output_name, self.default_aerodynamic_output_edit)
        if self.set_default_beam_output:
            self.link_definition(context, self.default_beam_output_name, self.default_beam_output_edit)
        self.entity.increment_links()
        exec("bpy.ops." + root_dot + "save('INVOKE_DEFAULT')")
    def draw(self, context):
        self.basis = (self.forever, self.set_method, self.set_nonlinear_solver, self.set_eigenanalysis, self.set_abort_after, self.set_linear_solver, self.set_dummy_steps, self.set_real_time, self.set_assembly, self.set_default_output, self.set_default_aerodynamic_output, self.set_default_beam_output)
        layout = self.layout
        layout.prop(self, "executable_path")
        layout.prop(self, "initial_time")
        row = layout.row()
        row.prop(self, "forever")
        if not self.forever:
            row.prop(self, "final_time")
        self.draw_link(layout, "general_data_name", "general_data_edit", "definition")
        row = layout.row()
        row.prop(self, "set_method")
        if self.set_method:
            self.draw_link(row, "method_name", "method_edit", "definition")
        row = layout.row()
        row.prop(self, "set_nonlinear_solver")
        if self.set_nonlinear_solver:
            self.draw_link(row, "nonlinear_solver_name", "nonlinear_solver_edit", "definition")
        row = layout.row()
        row.prop(self, "set_eigenanalysis")
        if self.set_eigenanalysis:
            self.draw_link(row, "eigenanalysis_name", "eigenanalysis_edit", "definition")
        row = layout.row()
        row.prop(self, "set_abort_after")
        if self.set_abort_after:
            self.draw_link(row, "abort_after_name", "abort_after_edit", "definition")
        row = layout.row()
        row.prop(self, "set_linear_solver")
        if self.set_linear_solver:
            self.draw_link(row, "linear_solver_name", "linear_solver_edit", "definition")
        row = layout.row()
        row.prop(self, "set_dummy_steps")
        if self.set_dummy_steps:
            self.draw_link(row, "dummy_steps_name", "dummy_steps_edit", "definition")
        self.draw_link(layout, "output_data_name", "output_data_edit", "definition")
        row = layout.row()
        row.prop(self, "set_real_time")
        if self.set_real_time:
            self.draw_link(row, "real_time_name", "real_time_edit", "definition")
        row = layout.row()
        row.prop(self, "set_assembly")
        if self.set_assembly:
            self.draw_link(row, "assembly_name", "assembly_edit", "definition")
        self.draw_link(layout, "job_control_name", "job_control_edit", "definition")
        row = layout.row()
        row.prop(self, "set_default_output")
        if self.set_default_output:
            self.draw_link(row, "default_output_name", "default_output_edit", "definition")
        row = layout.row()
        row.prop(self, "set_default_aerodynamic_output")
        if self.set_default_aerodynamic_output:
            self.draw_link(row, "default_aerodynamic_output_name", "default_aerodynamic_output_edit", "definition")
        row = layout.row()
        row.prop(self, "set_default_beam_output")
        if self.set_default_beam_output:
            self.draw_link(row, "default_beam_output_name", "default_beam_output_edit", "definition")
    def check(self, context):
        return self.basis != (self.forever, self.set_method, self.set_nonlinear_solver, self.set_eigenanalysis, self.set_abort_after, self.set_linear_solver, self.set_dummy_steps, self.set_real_time, self.set_assembly, self.set_default_output, self.set_default_aerodynamic_output, self.set_default_beam_output)
    def create_entity(self):
        return InitialValue(self.name)

klasses[InitialValueOperator.bl_label] = InitialValueOperator

class Save(bpy.types.Operator, Base):
    bl_idname = root_dot + "save"
    bl_options = {'REGISTER', 'INTERNAL'}
    bl_label = "Save Blender File"
    filter_glob = bpy.props.StringProperty(
            default="*.blend",
            options={'HIDDEN'},
            )
    filepath = bpy.props.StringProperty()
    def invoke(self, context, event):
        if not context.blend_data.filepath:
            self.filepath = "untitled.blend"
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}
        self.filepath = context.blend_data.filepath
        return self.execute(context)
    def execute(self, context):
        directory = os.path.splitext(self.filepath)[0]
        if not os.path.exists(directory):
            os.mkdir(directory)
        database.simulator[context.scene.simulator_index].write_input_file(context, directory)
        bpy.ops.wm.save_mainfile(filepath=self.filepath)
        context.scene.dirty_simulator = False
        context.scene.clean_log = False
        return{'PASS_THROUGH'}
BPY.klasses.append(Save)

class Simulate(bpy.types.Operator, Base):
    bl_idname = root_dot + "simulate"
    bl_options = {'REGISTER', 'INTERNAL'}
    bl_label = "Run simulation"
    bl_description = "Run MBDyn for the input file"
    def modal(self, context, event):
        wm = context.window_manager
        poll = self.process.poll()
        if poll == None:
            output = subprocess.check_output(("tail", "-n", "1", self.out_file))
            if output and 2 < len(output.split()):
                percent = 100.*(1.-(self.t_final - float(output.split()[2]))/self.t_range)
                wm.progress_update(percent)
            return {'PASS_THROUGH'}
        self.f.seek(0)
        s = self.f.read().decode()
        self.f.close()
        if poll:
            self.report({'ERROR'}, s)
        else:
            context.scene.clean_log = True
            BPY.plot_data = dict()
            if s:
                self.report({'INFO'}, s)
        wm.event_timer_remove(self.timer)
        wm.progress_end()
        return {'FINISHED'}
    def execute(self, context):
        sim = database.simulator[context.scene.simulator_index]
        directory = os.path.splitext(context.blend_data.filepath)[0]
        command = [sim.executable_path, "-s", "-f", os.path.join(directory, context.scene.name + ".mbd")]
        print(" ".join(command))
        self.f = TemporaryFile()
        self.process = subprocess.Popen(command, stdout=self.f, stderr=self.f)
        self.out_file = os.path.join(directory, context.scene.name + ".out")
        self.t_final = sim.final_time if not sim.forever else float("inf")
        self.t_range = self.t_final - sim.initial_time
        subprocess.call(("touch", self.out_file))
        wm = context.window_manager
        wm.progress_begin(0., 100.)
        self.timer = wm.event_timer_add(0.01, context.window)
        wm.modal_handler_add(self)
        return{'RUNNING_MODAL'}
BPY.klasses.append(Simulate)

class Animate(bpy.types.Operator, Base):
    bl_idname = root_dot + "animate"
    bl_options = {'REGISTER', 'INTERNAL'}
    bl_label = "Animate objects"
    bl_description = "Import results into Blender animation starting at the next frame"
    steps = bpy.props.IntProperty(name="Steps between animation", default=1, min=1)
    def invoke(self, context, event):
        scene = context.scene
        directory = os.path.splitext(context.blend_data.filepath)[0]
        for node in database.node:
            for data_path in "location rotation_euler".split():
                node.keyframe_insert(data_path)
        with open(os.path.join(directory, context.scene.name + ".mov")) as f:
            self.lines = f.readlines()
        self.marker = int(self.lines[0].split()[0])
        self.N = float(len(self.lines))
        for self.i, line in enumerate(self.lines[1:]):
            if int(line.split()[0]) == self.marker:
                break
        return context.window_manager.invoke_props_dialog(self)
    def execute(self, context):
        scene = context.scene
        frame_initial = scene.frame_current
        wm = context.window_manager
        wm.progress_begin(0., 100.)
        skip = self.steps - 1
        for n, line in enumerate(self.lines):
            if int(line.split()[0]) == self.marker:
                skip = (skip + 1) % self.steps
            if not skip:
                wm.progress_update(100.*float(n)/self.N)
                fields = line.split()
                node_index = int(fields[0])
                if node_index == self.marker:
                    scene.frame_current += 1
                fields = [float(field) for field in fields[1:13]]
                euler = Matrix([fields[3:6], fields[6:9], fields[9:12]]).to_euler()
                database.node[node_index].location = fields[:3]
                database.node[node_index].rotation_euler = euler[0], euler[1], euler[2]
                for data_path in "location rotation_euler".split():
                    database.node[node_index].keyframe_insert(data_path)
        scene.frame_current = frame_initial + 1
        wm.progress_end()
        return{'FINISHED'}
    def draw(self, context):
        layout = self.layout
        layout.label("File has " + str(int(self.N/(self.i+1))) + " timesteps.")
        layout.prop(self, "steps")
BPY.klasses.append(Animate)

bundle = Bundle(tree, Base, klasses, database.simulator, "simulator")
