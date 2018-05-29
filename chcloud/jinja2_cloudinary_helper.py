# encoding=utf-8
import json
import os

from flask import url_for

from jinja2.ext import Extension
from jinja2 import nodes, Template

import cloudinary


class CloudinaryURLExtension(Extension):
    tags = {'cloudinary_url'}

    def parse(self, parser):
        lineno = next(parser.stream).lineno

        options = dict()

        # Parse the arguments
        source = parser.parse_expression()

        if parser.stream.skip_if('comma'):
            first = True
            while parser.stream.current.type != 'block_end':
                if not first:
                    parser.stream.expect('comma')
                first = False

                # Lookahead to see if this is an assignment (an option)
                if parser.stream.current.test('name') and parser.stream.look().test('assign'):
                    name = next(parser.stream).value
                    parser.stream.skip()
                    value = parser.parse_expression()

                    options[nodes.Const(name)] = value

        node_options = []
        for k, v in options.items():
            node_options.append(nodes.Pair(k, v))

        node_options = nodes.Dict(node_options)

        call = self.call_method('render', [source, node_options], lineno=lineno)
        output = nodes.CallBlock(call, [], [], [])
        output.set_lineno(lineno)

        return output

    def render(self, source, options, caller=None):
        if not isinstance(source, cloudinary.CloudinaryResource):
            source = cloudinary.CloudinaryResource(source)

        return source.build_url(**options)


class CloudinaryTagExtension(CloudinaryURLExtension):
    tags = {'cloudinary'}

    def render(self, image, options, caller=None):
        if not isinstance(image, cloudinary.CloudinaryResource):
            image = cloudinary.CloudinaryResource(image)

        return image.image(**options)

