import os
import numpy as np
import re

from robosuite.models.objects import MujocoXMLObject

import pathlib

from libero.libero.envs.base_object import (
    register_object,
)

absolute_path = pathlib.Path(__file__).parent.parent.parent.absolute()


class CustomObjects(MujocoXMLObject):
    def __init__(self, custom_path, name, obj_name, joints=[dict(type="free", damping="0.0005")]):
        # make sure custom path is an absolute path
        assert(os.path.isabs(custom_path)), "Custom path must be an absolute path"
        # make sure the custom path is also an xml file
        assert(custom_path.endswith(".xml")), "Custom path must be an xml file"
        super().__init__(
            custom_path,
            name=name,
            joints=joints,
            obj_type="all",
            duplicate_collision_geoms=False,
        )
        self.category_name = "_".join(
            re.sub(r"([A-Z])", r" \1", self.__class__.__name__).split()
        ).lower()
        self.object_properties = {"vis_site_names": {}}


@register_object
class RedSticker(CustomObjects):
    def __init__(self,
                 name="red_sticker",
                 obj_name="red_sticker",
                 ):
        super().__init__(
            custom_path=os.path.abspath(os.path.join(
                os.path.dirname(__file__), "../../../../notebooks/custom_assets/red_sticker/red_sticker.xml"
            )),
            name=name,
            obj_name=obj_name,
        )

        # Keep the cylinder fully upright.
        self.rotation = {
            "x": (0.0, 0.0),          # No x-axis rotation; keep upright.
            "y": (0.0, 0.0),          # No y-axis rotation; keep upright.
            "z": (0.0, 0.0),          # No z-axis rotation; keep the orientation fixed.
        }
        self.rotation_axis = "z"  # Set z as the main rotation axis.
        
        # Keep fully upright without an init_quat that forces rotation.
        
        
@register_object
class BlueRedSticker(CustomObjects):
    def __init__(self,
                 name="blue_red_sticker",
                 obj_name="blue_red_sticker",
                 ):
        super().__init__(
            custom_path=os.path.abspath(os.path.join(
                os.path.dirname(__file__), "../../../../notebooks/custom_assets/blue_red_sticker/blue_red_sticker.xml"
            )),
            name=name,
            obj_name=obj_name,
        )
        
        # Keep the cylinder fully upright.
        self.rotation = {
            "x": (0.0, 0.0),          # No x-axis rotation; keep upright.
            "y": (0.0, 0.0),          # No y-axis rotation; keep upright.
            "z": (0.0, 0.0),          # No z-axis rotation; keep the orientation fixed.
        }
        self.rotation_axis = "z"  # Set z as the main rotation axis.
        
        # Keep fully upright without an init_quat that forces rotation.


@register_object
class RedBox(CustomObjects):
    def __init__(self,
                 name="red_box",
                 obj_name="red_box",
                 ):
        super().__init__(
            custom_path=os.path.abspath(os.path.join(
                os.path.dirname(__file__), "../../../../notebooks/custom_assets/red_box/red_box.xml"
            )),
            name=name,
            obj_name=obj_name,
        )

        self.rotation = {
            "x": (-np.pi/2, -np.pi/2),
            "y": (-np.pi, -np.pi),
            "z": (np.pi, np.pi),
        }
        self.rotation_axis = None



@register_object
class LiberoMugYellow(CustomObjects):
    def __init__(self,
                 name="libero_mug_yellow",
                 obj_name="libero_mug_yellow",
                 ):
        super().__init__(
            custom_path=os.path.abspath(os.path.join(
                os.path.dirname(__file__), "../../../../notebooks/custom_assets/libero_mug_yellow/libero_mug_yellow.xml"
            )),
            name=name,
            obj_name=obj_name,
        )

        self.rotation = {
            "x": (-np.pi/2, -np.pi/2),
            "y": (-np.pi, -np.pi),
            "z": (np.pi, np.pi),
        }
        self.rotation_axis = None

@register_object
class LiberoMugGreen(CustomObjects):
    def __init__(self,
                 name="libero_mug_green",
                 obj_name="libero_mug_green",
                 ):
        super().__init__(
            custom_path=os.path.abspath(os.path.join(
                os.path.dirname(__file__), "../../../../notebooks/custom_assets/libero_mug_green/libero_mug_green.xml"
            )),
            name=name,
            obj_name=obj_name,
        )

        self.rotation = {
            "x": (-np.pi/2, -np.pi/2),
            "y": (-np.pi, -np.pi),
            "z": (np.pi, np.pi),
        }
        self.rotation_axis = None
