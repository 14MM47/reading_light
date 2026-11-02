"""kigen: generate KiCad 9 schematics and boards from a Python design description.

Modules:
  sexpr     - S-expression parser/serializer for KiCad files
  symlib    - load (and flatten) symbols from .kicad_sym libraries, pin geometry
  schematic - write a .kicad_sch with embedded symbols, wire stubs and net labels
  board     - build a .kicad_pcb with pcbnew (footprints, nets, outline, zones)
  router    - small 2-layer grid A* router used on these boards
"""
