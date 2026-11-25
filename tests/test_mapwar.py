import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np

from engine.mapwar import eggfield, field, qchar, qrig
from engine.mapwar.mapshot import MapShot
from engine.mapwar.world import World


class MapWarTest(unittest.TestCase):
    def test_custom_map_changes_owner_without_relief_raster(self):
        land = {
            'type': 'Feature',
            'properties': {},
            'geometry': {'type': 'Polygon', 'coordinates': [
                [[0, 0], [6, 0], [6, 4], [0, 4], [0, 0]],
            ]},
        }
        with TemporaryDirectory() as tmp:
            for layer, features in [('ne_50m_land', [land]), ('ne_10m_lakes', []),
                                    ('ne_10m_rivers_lake_centerlines', [])]:
                (Path(tmp) / f'{layer}.geojson').write_text(
                    json.dumps({'type': 'FeatureCollection', 'features': features}),
                )
            world = World(dict(
                bbox=(0, 6, 0, 4), px_per_deg=80, relief_raster=False,
                sides={0: dict(ink=(.5, .2, .15)), 1: dict(ink=(.15, .3, .5))},
                cities=[('A', 1, 2, 0, 0), ('B', 4, 2, 1, 0)],
                flips={'B': [(1, 0)]},
            ), tmp)
            self.assertFalse(world.ELEV.any())
            self.assertEqual(world.city_state(1, .5)[1], 1)
            self.assertEqual(world.city_state(1, 1.2)[1], 0)
            shot = MapShot(world, dict(hud=dict(share=False)))
            self.assertEqual(shot.frame(1.2).size, (1920, 1080))

    def test_eggfield_can_render_without_an_impact(self):
        default_units = tuple(eggfield.UNITS)
        unit = eggfield.Unit('H', 'spear', 2, 3, 1.1, [(0, 4, 0, 180)])
        result = eggfield.simulate([unit])
        self.assertEqual(tuple(eggfield.UNITS), default_units)
        self.assertIsNone(result['imp'])
        image, _, t = eggfield.render(.15, result, [(0, 0, 0, 24, 48, 90, 0)])
        self.assertEqual(t, .15)
        self.assertEqual(image.size, (1920, 1080))

    def test_character_joint_coordinates(self):
        surf, ctx = field.canvas()
        spec = dict(head='round', gear='headband', robe=(.22, .32, .46))
        joints, pose, scale = qchar.Q(ctx, 960, 880, 480, spec, name='run', t=.15)
        self.assertTrue(np.isfinite(qrig.to_world(pose, scale, joints['hdf'])).all())
        qchar.rider(ctx, 1420, 820, 340, spec, t=.15)
        qrig.head(ctx, 470, 350, 140, spec, dict(front=True, eye='closed'))
        surf.flush()
        self.assertTrue(np.frombuffer(surf.get_data(), np.uint8).any())
