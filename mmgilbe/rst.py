# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - ReStructured Text Parser

    @copyright: 2002 by J�rgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
    
    REQUIRES cvs version of docutils of at least 03_22_2004
    .
"""

#############################################################################
### ReStructured Text Parser
#############################################################################


import sys
import os
import os.path
import time
import re
from types import ListType

import docutils
from docutils import core, frontend, nodes, utils, writers, languages
from docutils.core import publish_string
from docutils.writers import html4css1


def html_escape_unicode(node):
    # Find Python function that does this for me. string.encode('ascii',
    # 'xmlcharrefreplace') only 2.3 and above.
    s = node.replace(u'\xa0', '&#xa0;')
    return s.replace(u'\u2020', '&#x2020;')

class MoinWriter(html4css1.Writer):
    
    config_section = 'moin writer'
    config_section_dependencies = ('writers',)

    """Final translated form of `document`."""
    output = None
    
    def wiki_resolver(self, node):
        # If the node has an 'id' attribute then it is an implicit hyperlink
        # that we shouldn't make into a moin link.
        if 'id' in node.attributes:
            return 0
        node['refuri'] = node['refname']
        del node['refname']
        return '1'
    
    wiki_resolver.priority = 001
    
    def __init__(self, formatter, request):
        html4css1.Writer.__init__(self)
        self.formatter = formatter
        self.request = request
        # Add our wiki unknown_reference_resolver to our list of functions to
        # run when a target isn't found
        self.unknown_reference_resolvers = [self.wiki_resolver]
        # We create a new parser to process MoinMoin wiki style links in the 
        # restructured text.
        from MoinMoin.parser.wiki import Parser
        self.wikiparser = Parser('', self.request)
        self.wikiparser.formatter = self.formatter
        self.wikiparser.hilite_re = None
        
        
    def translate(self):
        visitor = MoinTranslator(self.document, 
                                 self.formatter, 
                                 self.request,
                                 self.wikiparser)
        self.document.walkabout(visitor)
        self.output = html_escape_unicode(visitor.astext())
        

# TODO: This would be easier to sub class the real moin wiki parser.
class Parser:
    def __init__(self, raw, request, **kw):
        self.raw = raw
        self.request = request
        self.form = request.form
        
    def format(self, formatter):
        text = publish_string(source = self.raw, 
                              writer = MoinWriter(formatter, self.request),
                              enable_exit = None, 
                              settings_overrides = {'traceback': 1})
        self.request.write(html_escape_unicode(text))
        

class MoinTranslator(html4css1.HTMLTranslator):

    def __init__(self, document, formatter, request, parser):
        html4css1.HTMLTranslator.__init__(self, document)
        self.formatter = formatter
        self.request = request
        self.level = 0
        # We supply our own request.write so that the html is added to the
        # html4css1 body list instead of printed to stdout.
        self.old_write = self.request.write
        self.request.write = self.rst_write
        self.wikiparser = parser
        self.wikiparser.request = request
        self.wikiparser.request.write = self.rst_write
        # When we use MoinMoin to interpret a MoinMoin refuri we want to strip
        # the paragraph tags to keep the correct formatting.
        self.strip_paragraph = 0
        
    def astext(self):
        self.request.write = self.old_write
        return html4css1.HTMLTranslator.astext(self)
    
    def rst_write(self, string):
        f = open('/tmp/mlog', 'w')
        if self.strip_paragraph:
            string = string.replace('<p>', '')
            string = string.replace('</p>', '')
            string = string.replace('\n', '')
            if len(string) and string[-1] == ' ':
                string = string[:-1]
            print 'asdf', `string`
        f.write(string)
        self.body.append(string)
        
    def visit_section(self, node):
        self.level += 1

    def depart_section(self, node):
        self.level -= 1

    def visit_title(self, node):
        self.request.write(self.formatter.heading(self.level, '', on=1))

    def depart_title(self, node):
        self.request.write(self.formatter.heading(self.level, '', on=0))
        
    def visit_reference(self, node):
        if 'refuri' in node.attributes:
            # Set this if our test handles the node
            handled = 0
            # We don't want these pieces wrapped in <p> tags, I think.
            self.strip_paragraph = 1
            # Unless the user has explicitly added the type of the uri then we
            # let MoinMoin handle it.
            if ':' not in node['refuri']:
                # The node should have a whitespace normalized name if the
                # docutlis restructured text parser would normally fully
                # normalize the name.
                if 'name' in node.attributes:
                    self.wikiparser.raw = '[:%s: %s]' % (node['name'], 
                                                         node.astext())
                else:
                    self.wikiparser.raw = '[:%s: %s]' % (node['refuri'], 
                                                         node.astext())

                self.wikiparser.format(self.formatter)
                handled = 1
            self.strip_paragraph = 0
            if handled:
                raise docutils.nodes.SkipNode
                return
        html4css1.HTMLTranslator.visit_reference(self, node)

    #
    # Text markup
    #

    def visit_emphasis(self, node):
        self.request.write(self.formatter.emphasis(1))

    def depart_emphasis(self, node):
        self.request.write(self.formatter.emphasis(0))

    def visit_strong(self, node):
        self.request.write(self.formatter.strong(1))

    def depart_strong(self, node):
        self.request.write(self.formatter.strong(0))

    def visit_literal(self, node):
        self.request.write(self.formatter.code(1))

    def depart_literal(self, node):
        self.request.write(self.formatter.code(0))


    #
    # Blocks
    #

    def visit_literal_block(self, node):
        self.request.write(self.formatter.preformatted(1))

    def depart_literal_block(self, node):
        self.request.write(self.formatter.preformatted(0))


    #
    # Simple Lists
    #

    def visit_bullet_list(self, node):
        self.request.write(self.formatter.bullet_list(1))

    def depart_bullet_list(self, node):
        self.request.write(self.formatter.bullet_list(0))

    def visit_enumerated_list(self, node):
        self.request.write(self.formatter.number_list(1, start=node.get('start', None)))

    def depart_enumerated_list(self, node):
        self.request.write(self.formatter.number_list(0))

    def visit_list_item(self, node):
        self.request.write(self.formatter.listitem(1))

    def depart_list_item(self, node):
        self.request.write(self.formatter.listitem(0))


    #
    # Definition List
    #

    def visit_definition_list(self, node):
        self.request.write(self.formatter.definition_list(1))

    def depart_definition_list(self, node):
        self.request.write(self.formatter.definition_list(0))


    #
    # Admonitions
    #

    def visit_warning(self, node):
        self.request.write(self.formatter.highlight(1))

    def depart_warning(self, node):
        self.request.write(self.formatter.highlight(0))

