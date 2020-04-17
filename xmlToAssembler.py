#!/usr/bin/python
import xml.etree.ElementTree as ET

def main():
   root = ET.parse('instructions.xml')

   print '.intel_syntax noprefix'
   for instrNode in root.iter('instruction'):
      # Future instruction set extensions
      if instrNode.attrib['extension'] in ['CLDEMOTE', 'ENQCMD', 'MCOMMIT', 'MOVDIR', 'PCONFIG', 'RDPRU', 'SERIALIZE', 'SNP', 'TSX_LDTRK', 'WAITPKG', 'WBNOINVD']:
         continue
      if any(x in instrNode.attrib['isa-set'] for x in ['BF16_', 'VP2INTERSECT']):
         continue

      asm = instrNode.attrib['asm']
      first = True
      for operandNode in instrNode.iter('operand'):
         operandIdx = int(operandNode.attrib['idx'])

         if operandNode.attrib.get('suppressed', '0') == '1':
            continue;

         if not first and not operandNode.attrib.get('opmask', '') == '1':
            asm += ', '
         else:
            asm += ' '
            first = False

         if operandNode.attrib['type'] == 'reg':
            registers = operandNode.text.split(',')
            register = registers[min(operandIdx, len(registers)-1)]
            if not operandNode.attrib.get('opmask', '') == '1':
               asm += register
            else:
               asm += '{' + register + '}'
               if instrNode.attrib.get('zeroing', '') == '1':
                  asm += '{z}'
         elif operandNode.attrib['type'] == 'mem':
            memoryPrefix = operandNode.attrib.get('memory-prefix', '')
            if memoryPrefix:
               asm += memoryPrefix + ' '

            if operandNode.attrib.get('VSIB', '0') != '0':
               asm += '[' + operandNode.attrib.get('VSIB') + '0]'
            else:
               asm += '[RAX]'

            memorySuffix = operandNode.attrib.get('memory-suffix', '')
            if memorySuffix:
               asm += ' ' + memorySuffix
         elif operandNode.attrib['type'] == 'agen':
            agen = instrNode.attrib['agen']
            address = []

            if 'R' in agen: address.append('RIP')
            if 'B' in agen: address.append('RAX')
            if 'I' in agen: address.append('2*RBX')
            if 'D' in agen: address.append('8')

            asm += ' [' + '+'.join(address) + ']'
         elif operandNode.attrib['type'] == 'imm':
            if instrNode.attrib.get('roundc', '') == '1':
               asm += '{rn-sae}, '
            elif instrNode.attrib.get('sae', '') == '1':
               asm += '{sae}, '
            width = int(operandNode.attrib['width'])
            if operandNode.attrib.get('implicit', '') == '1':
               imm = operandNode.text
            else:
               imm = (1 << (width-8)) + 1
            asm += str(imm)
         elif operandNode.attrib['type'] == 'relbr':
            asm = '1: ' + asm + '1b'

      if not 'sae' in asm:
         if instrNode.attrib.get('roundc', '') == '1':
            asm += ', {rn-sae}'
         elif instrNode.attrib.get('sae', '') == '1':
            asm += ', {sae}'

      print asm

if __name__ == "__main__":
    main()
