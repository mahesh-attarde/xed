#!/usr/bin/python
import xml.etree.ElementTree as ET
from collections import defaultdict
from operator import itemgetter

def main():
   root = ET.parse('instructions.xml')
   
   attributes = ['iform', 'eosz', 'rex', 'rep', 'zeroing', 'mask', 'bcast', 'sae']   
   allIformCombinations = [itemgetter(*attributes)(defaultdict(lambda: 0, instrNode.attrib)) for instrNode in root.iter('instruction')]
   
   assert(len(allIformCombinations) == len(set(allIformCombinations)))

if __name__ == "__main__":
    main()
