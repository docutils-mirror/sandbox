"""
implement aafigure directive
"""

import os, sys, tempfile, popen2
import aafigure, svg

from docutils import nodes
from docutils.parsers.rst.directives import register_directive

aafigure_counter = 0

def AAFigureDrective (name, arguments, options, content, lineno,
                  content_offset, block_text, state, state_machine):
    text = '\n'.join(content)
    
    global aafigure_counter
    aafigure_counter += 1
    output_path = '.'
    print output_path
    output_name = os.path.join(output_path, 'aafigure-%i.svg' % aafigure_counter)
    
    aaimg = aafigure.AsciiArtImage(text)
    #~ print text
    aaimg.recognize()
    svgout = svg.SVGOutputVisitor(
        file(output_name, 'w'),
        scale = 10,
        debug = True
    )
    svgout.visit(aaimg)

    # Return an image directive.
    #~ options['uri'] = os.path.basename(output_name)
    #~ return [nodes.image(output_name, **options)]
    
    attributes = {'format': 'html'}
    return [nodes.raw('', '<embed src="%s" %s/>' % (
            output_name,
            svgout.get_size_attrs()
        ), **attributes)]

AAFigureDrective.content = True

def register():
    register_directive('aafigure', AAFigureDrective)
