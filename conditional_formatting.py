import bpy


conditions = [
    {
        "type": "Name",
        "conditions": [
            "Is",
            "Is Not",
            "Starts With",
            "Ends With",
            "Contains"
        ],
        "function": "evaluate_name"
    },
    {
        "type": "Belongs To",
        "conditions": [
            "Collection",
        ],
        "function": "evaluate_belongs_to"
    },
    {
        "type": "Poly Count",
        "conditions": [
            "Greater Than",
            "Less Than"
        ],
        "function": "evaluate_polygon_count"
    }
]


def evaluate_name(condition, value):
    print(condition, value)
    if condition == get_enum_string("Is"):
        return [obj for obj in bpy.context.scene.objects if obj.name == value]
    
    elif condition == get_enum_string("Is Not"):
        return [obj for obj in bpy.context.scene.objects if obj.name != value]
    
    elif condition == get_enum_string("Starts With"):
        return [obj for obj in bpy.context.scene.objects if obj.name.startswith(value)]
    
    elif condition == get_enum_string("Ends With"):
        return [obj for obj in bpy.context.scene.objects if obj.name.endswith(value)]
    
    elif condition == get_enum_string("Contains"):
        return [obj for obj in bpy.context.scene.objects if value in obj.name]
    
    else:
        raise NotImplementedError("Condition not valid or not implemented")


def evaluate_belongs_to(condition, value):
    print(condition, value)
    if condition == get_enum_string("Collection"):
        return [obj for obj in bpy.context.scene.objects \
            if obj.name in bpy.data.collections[value].objects]
            
    else:
        raise NotImplementedError("Condition not valid or not implemented")


def evaluate_polygon_count(condition, value):
    print(condition, value)
    if condition == get_enum_string("Greater Than"):
        return [obj for obj in bpy.context.scene.objects \
            if len(obj.data.polygons) > int(value)]
            
    elif condition == get_enum_string("Less Than"):
        return [obj for obj in bpy.context.scene.objects \
            if len(obj.data.polygons) < int(value)]
            
    else:
        raise NotImplementedError("Condition not valid or not implemented")


def get_enum_string(text):
    return text.upper().replace(" ",  "_")


def get_conditions(self, context):
    for condition in conditions:
        if condition["type"].upper().replace(" ",  "_") == self.evaluate:
            return [(get_enum_string(con), con, "", i+1) \
                for i, con in enumerate(condition["conditions"])]
                
                
def get_evaluator(condition_type):
    for condition in conditions:
        if get_enum_string(condition["type"]) == condition_type:
            return condition["function"]
                

def execute_rule(rule):
    evaluator = globals()[get_evaluator(rule.evaluate)]
    print(evaluator(rule.condition, rule.value))
    for obj in evaluator(rule.condition, rule.value):
        obj.display_type = rule.output


def execute_all_rules(scene):
    for rule in bpy.context.scene.rules:
        execute_rule(rule)
    

class Rule(bpy.types.PropertyGroup):
    evaluate: bpy.props.EnumProperty(
        items=[
            (get_enum_string(condition["type"]), condition["type"], "", i+1) \
                for i, condition in enumerate(conditions)
        ],
        default=1,
    )
    
    condition: bpy.props.EnumProperty(
        items=get_conditions,
        default=1,
    )
    
    value: bpy.props.StringProperty()
    
    output: bpy.props.EnumProperty(
        items=[
            ("SOLID", "Display as Solid", "", 1),
            ("WIRE", "Display as Wire", "", 2),
            ("BOUNDS", "Display as Bounds", "", 3),
        ],
    )


class AddRule(bpy.types.Operator):
    bl_idname = "scene.add_rule"
    bl_label = "Add Rule"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        rule = bpy.context.scene.rules.add()
        execute_rule(rule, context)
        return {'FINISHED'}


class AddRule(bpy.types.Operator):
    bl_idname = "scene.add_rule"
    bl_label = "Add Rule"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        rule = bpy.context.scene.rules.add()
        execute_rule(rule)
        return {'FINISHED'}


class RemoveRule(bpy.types.Operator):
    bl_idname = "scene.remove_rule"
    bl_label = "Remove Rule"
    bl_options = {'REGISTER', 'UNDO'}
    
    index: bpy.props.IntProperty()
    
    def execute(self, context):
        bpy.context.scene.rules.remove(self.index)
        execute_all_rules(context.scene)
        return {'FINISHED'}


class LayoutDemoPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "Conditional Formatting"
    bl_idname = "SCENE_PT_layout"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        rules = context.scene.rules
        
        for i, rule in enumerate(rules):
            box = layout.box()
            col = box.column()
            row = col.row()
            row.label(text=f"  Rule #{i+1}")
            row.split(factor=0.9)
            row.operator("scene.remove_rule", icon="X", text="", emboss=False).index = i
            col.separator()
            col.prop(rule, "evaluate", text="Evaluate")
            col.prop(rule, "condition", text="Condition")
            col.prop(rule, "value", text="Value")
            col.prop(rule, "output", text="Action")
            col.separator()

        layout.operator("scene.add_rule", icon='ADD')


classes = [
    Rule,
    AddRule,
    RemoveRule,
    LayoutDemoPanel,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.rules = bpy.props.CollectionProperty(type=Rule)
    
    for handler in bpy.app.handlers.depsgraph_update_post:
        if hasattr(handler, "conditional"):
            bpy.app.handlers.depsgraph_update_post.remove(handler)
            break
    
    bpy.app.handlers.depsgraph_update_post.append(execute_all_rules)
    bpy.app.handlers.depsgraph_update_post[-1].__dict__["conditional"] = True


def unregister():
    del bpy.types.Scene.rules
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
