"""For various utilities that are shared between modules"""
from dataclasses import dataclass
import os


@dataclass()
class HOI4Directory:
    root: str

    def common(self):
        return os.path.join(self.root, 'common')

    def units(self):
        return os.path.join(self.common(), 'units')

    def equipment(self):
        return os.path.join(self.units(), 'equipment')
