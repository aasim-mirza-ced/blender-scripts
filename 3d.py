import bpy
import json
import math

# Class for creating a wall
class Wall:
    def __init__(self, name, location, scale, rotation):
        self.name = name
        self.location = location
        self.scale = scale
        self.rotation = rotation
        self.object = self.create_wall()

    def create_wall(self):
        bpy.ops.mesh.primitive_plane_add(size=2, location=self.location)
        wall = bpy.context.object
        wall.name = self.name
        wall.scale[0] = self.scale[0]
        wall.scale[1] = self.scale[1]
        wall.rotation_euler = self.rotation
        return wall

    def add_cutout(self, cutout_object, operation='DIFFERENCE'):
        bpy.context.view_layer.objects.active = self.object
        bpy.ops.object.modifier_add(type='BOOLEAN')
        boolean_mod = self.object.modifiers[-1]
        boolean_mod.operation = operation
        boolean_mod.object = cutout_object
        bpy.ops.object.modifier_apply(modifier=boolean_mod.name)

    def shade_smooth(self):
        self.object.select_set(True)
        bpy.ops.object.shade_smooth()

# Class for creating a door or window cutout
class Cutout:
    def __init__(self, name, location, scale):
        self.name = name
        self.location = location
        self.scale = scale
        self.object = self.create_cutout()

    def create_cutout(self):
        bpy.ops.mesh.primitive_cube_add(size=2, location=self.location)
        cutout = bpy.context.object
        cutout.name = self.name
        cutout.scale[0] = self.scale[0]
        cutout.scale[1] = self.scale[1]
        cutout.scale[2] = self.scale[2]
        return cutout

# Class for creating a ceiling fan
class CeilingFan:
    def __init__(self, location, blade_count, blade_offset, blade_length, blade_width):
        self.location = location
        self.blade_count = blade_count
        self.blade_offset = blade_offset
        self.blade_length = blade_length
        self.blade_width = blade_width
        self.motor_housing = self.create_motor_housing()
        self.blades = self.create_blades()
        self.join_parts()

    def create_motor_housing(self):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.5, location=self.location)
        motor_housing = bpy.context.object
        motor_housing.name = "MotorHousing"
        return motor_housing

    def create_blade(self, location, rotation):
        bpy.ops.mesh.primitive_plane_add(size=1, location=location)
        blade = bpy.context.object
        blade.name = "FanBlade"
        blade.scale[0] = self.blade_length  # Length of the blade
        blade.scale[1] = self.blade_width  # Width of the blade
        blade.rotation_euler = rotation
        return blade

    def create_blades(self):
        blades = []
        blade_rotations = [(0, 0, math.radians(i * (360 / self.blade_count))) for i in range(self.blade_count)]
        for rotation in blade_rotations:
            location = (self.blade_offset * math.cos(rotation[2]), self.blade_offset * math.sin(rotation[2]), self.location[2])
            blade = self.create_blade(location, rotation)
            blades.append(blade)
        return blades

    def join_parts(self):
        bpy.ops.object.select_all(action='DESELECT')
        self.motor_housing.select_set(True)
        for blade in self.blades:
            blade.select_set(True)
        bpy.context.view_layer.objects.active = self.motor_housing
        bpy.ops.object.join()

# Class for creating a door or window
class DoorWindow:
    def __init__(self, wall, name, location, scale, material):
        self.wall = wall
        self.cutout = Cutout(name, location, scale)
        self.add_door_window(material)

    def add_door_window(self, material):
        self.wall.add_cutout(self.cutout.object)
        self.cutout.object.data.materials.append(material)
        self.wall.shade_smooth()

# Class for creating a door/window material
class DoorMaterial:
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.material = self.create_material()

    def create_material(self):
        mat = bpy.data.materials.new(name=self.name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs['Base Color'].default_value = (*self.color, 1)  # RGB color with alpha 1
        return mat

# Class for creating a room
class Room:
    def __init__(self, config):
        self.length = config['room']['length']
        self.width = config['room']['width']
        self.height = config['room']['height']
        self.floor_type = config['floor'].get('type', 'default')
        self.floor_type_file = config['floor'].get('path', 'default')
        self.create_floor()
        self.create_ceiling()
        self.create_walls(config['walls'])
        self.door_material = DoorMaterial("BrownDoorMaterial", (0.396, 0.267, 0.129)).material
        self.add_doors_and_windows(config['doors'], config['windows'])
        self.add_ceiling_fan(config['ceiling_fan'])

    def create_floor(self):
        bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
        floor = bpy.context.object
        floor.name = "Floor"
        floor.scale[0] = self.length / 2
        floor.scale[1] = self.width / 2

                  # Apply material based on floor type
        if self.floor_type == 'wooden':
            mat = bpy.data.materials.new(name="WoodenFloor")
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            tex_image = mat.node_tree.nodes.new("ShaderNodeTexImage")
            tex_type = bpy.data.images.load(self.floor_type_file)
            tex_image.image = tex_type
            mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])
            if floor.data.materials:
                floor.data.materials[0] = mat
            else:
                floor.data.materials.append(mat)
        self.floor = floor
        
    def create_ceiling(self):
        bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, self.height))
        ceiling = bpy.context.object
        ceiling.name = "Ceiling"
        ceiling.scale[0] = self.length / 2
        ceiling.scale[1] = self.width / 2
        self.ceiling = ceiling

    def create_walls(self, walls_config):
        self.walls = {}
        for wall in walls_config:
            new_wall = Wall(wall['name'], wall['location'], wall['scale'], wall['rotation'])
            self.walls[wall['name']] = new_wall

    def add_doors_and_windows(self, doors_config, windows_config):
        for door in doors_config:
            self.create_door(door)

        for window in windows_config:
            self.create_window(window)

    def create_door(self, door_config):
        door = DoorWindow(self.walls[door_config['wall']], door_config['name'], door_config['location'], door_config['scale'], self.door_material)

    def create_window(self, window_config):
        window = DoorWindow(self.walls[window_config['wall']], window_config['name'], window_config['location'], window_config['scale'], self.door_material)

    def add_ceiling_fan(self, fan_config):
        self.ceiling_fan = CeilingFan(
            fan_config['location'],
            fan_config['blade_count'],
            fan_config['blade_offset'],
            fan_config['blade_length'],
            fan_config['blade_width']
        )

# Load the configuration file
with open("C:/Users/CedAI/Desktop/data.json", 'r') as f:
    config = json.load(f)

# Create a room based on the configuration
room = Room(config)

# Switch to Material Preview mode
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'MATERIAL'
