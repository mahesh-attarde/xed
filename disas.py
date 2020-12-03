#!/usr/bin/python

import argparse
import re
import subprocess
import xml.etree.ElementTree as ET
from collections import defaultdict, deque, namedtuple

InstrDisas = namedtuple('InstrDisas', ['addr', 'opcode', 'asm', 'iform', 'regOperands', 'memOperands', 'rw', 'attributes'])
allXmlAttributes = ['agen', 'bcast', 'eosz', 'mask', 'rep', 'rex', 'sae', 'zeroing']

# Returns a list of InstrDisas tuples
def parseXedOutput(output, useIACAMarkers=False):
   output = re.sub('#.*\n', '', output)
   output = re.sub('Mapped.*\n', '', output)
   output = re.sub('RESETTING STATS', '', output)

   retList = []
   iacaStartMarkerFound = False
   prevOpcodes = deque(maxlen=3)
   for instrOutput in re.findall('([\s\S]*?XDIS.*\n)', output):
      instrOutput = instrOutput.strip()
      lines = instrOutput.splitlines()

      lastLine = lines[-1].split()
      addr = lastLine[1].replace(':', '')
      opcode = lastLine[4]

      if useIACAMarkers:
         prevOpcodes.appendleft(opcode)

         if iacaStartMarkerFound:
            if ''.join(prevOpcodes) == '0F0B646790BBDE000000':
               retList.pop()
               retList.pop()
               break
         else:
            if ''.join(prevOpcodes) == '646790BB6F0000000F0B':
               iacaStartMarkerFound = True
            continue

      tokensList = lines[0][re.match("\S* \S* ", lines[0]).end():].split(', ')
      tokens = {s[0]:(s[1] if len(s)>1 else '1') for x in tokensList for s in [x.split(':')]}

      memOperands = {k:v for k, v in tokens.items() if re.match('MEM\d|AGEN', k)}
      regOperands = {k:v for k, v in tokens.items() if re.match('REG\d', k)}

      attributes = {k:v for k, v in tokens.items()}
      if 'MASK' in attributes and attributes['MASK'] != '0':
         attributes['MASK'] = '1'
      if 'AGEN' in tokens:
         v = tokens['AGEN']
         agen = ''
         first = v.split('+')[0]
         if not '*' in first and not '0x' in first: agen += 'B'
         if 'RIP' in v: agen += 'R'
         if '*' in v: agen += 'I'
         if 'POS_DISP' in attributes: agen += 'D'
         attributes['AGEN'] = agen

      asm = lines[-2][6:]
      iform = lines[0].split()[1]

      rw = {}
      for line in lines[1:-2]:
         sp = line[3:].split('/')
         n, a = (sp[0], sp[-1])
         if n in memOperands or n in regOperands:
            rw[n] = a

      retList.append(InstrDisas(addr, opcode, asm, iform, regOperands, memOperands, rw, attributes))

   return retList


# Disassembles a binary and finds for each instruction the corresponding entry in the XML file.
# With the -iacaMarkers option, only the parts of the code that are between the IACA markers are considered.
def main():
   parser = argparse.ArgumentParser(description='Disassembler')
   parser.add_argument('xmlfile', help="XML file")
   parser.add_argument('filename', help="File to be disassembled")
   parser.add_argument("-iacaMarkers", help="Use IACA markers", action='store_true')
   args = parser.parse_args()

   output = subprocess.check_output(['obj/wkit/bin/xed', '-v', '4', '-i',  args.filename])
   disas = parseXedOutput(output, args.iacaMarkers)

   root = ET.parse(args.xmlfile)

   iformToXML = defaultdict(list)
   for XMLInstr in root.iter('instruction'):
      iformToXML[XMLInstr.attrib['iform']].append(XMLInstr)

   for instr in disas:
      for XMLInstr in iformToXML[instr.iform]:
         if all(instr.attributes.get(k.upper(), '0') == v for k, v in XMLInstr.attrib.items() if k in allXmlAttributes):
            print XMLInstr.attrib['string'] + ': ' + str(tuple(instr))
            break

if __name__ == "__main__":
    main()
