# -*- coding: utf-8 -*-
#  Copyright 2011 Takeshi KOMIYA
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from __future__ import division

import blockdiag.drawer
from blockdiag.utils import XY, Box

from nwdiag.metrics import DiagramMetrics


def _deautoscaler(obj):
    # At rendering with " --antialias", the object gotten via
    # DiagramMetrics might be wrapped by blockdiag.metrics.AutoScaler.
    # This function uses existence of 'original_metrics' attribute to
    # examine autoscale-ness instead of 'subject', because the former
    # is more blockdiag specific than the later.
    return getattr(obj, 'original_metrics', obj)


class DiagramDraw(blockdiag.drawer.DiagramDraw):
    def create_metrics(self, *args, **kwargs):
        return DiagramMetrics(*args, **kwargs)

    def __init__(self, _format, diagram, filename=None, **kwargs):
        super(DiagramDraw, self).__init__(_format, diagram, filename, **kwargs)
        self.drawer.set_options(jump_forward='vertical',
                            jump_radius=self.metrics.jump_radius,
                            jump_shift=self.metrics.jump_shift)

    @property
    def groups(self):
        return self.diagram.groups

    def pagesize(self, scaled=False):
        return super(DiagramDraw, self).pagesize(scaled).to_integer_point()

    def _draw_background(self):
        super(DiagramDraw, self)._draw_background()
        self.trunklines_shadow()

    def trunklines_shadow(self):
        for network in self.diagram.networks:
            if network.hidden is False and network.color != 'none':
                self.trunkline(network, shadow=True)

    def trunklines(self):
        metrics = self.metrics
        for network in self.diagram.networks:
            if network.hidden is False:
                self.trunkline(network)

                if (self.diagram.external_connector and
                   (network == self.diagram.networks[0])):
                    if network.trunk_diameter:
                        r = int(network.trunk_diameter) // 2
                    else:
                        r = metrics.trunk_diameter // 2

                    pt = metrics.network(network).top
                    pt0 = XY(pt.x, pt.y - metrics.span_height * 2 // 3)
                    pt1 = XY(pt.x, pt.y - r)

                    self.drawer.line([pt0, pt1], fill=network.linecolor)

    def trunkline(self, network, shadow=False):
        metrics = self.metrics
        m = metrics.network(network)

        #print(f"trunk diameter={metrics.trunk_diameter} and network.trunk_diameter={network.trunk_diameter} for network {network.id}")
        
        # Overload default trunk diameter if a specific value is given for this network
        if (network.trunk_diameter):
            r = int(network.trunk_diameter) // 2
        else:
            r = metrics.trunk_diameter // 2
        

        #print(f"Drawing trunkline with r={r} for network {network.id} and shadow {shadow}")

        pt1, pt2 = m.trunkline
        box = Box(pt1.x, pt1.y - r, pt2.x, pt2.y + r)

        if shadow:
            xdiff = self.metrics.shadow_offset.x
            ydiff = self.metrics.shadow_offset.y // 2

            box = Box(pt1.x + xdiff, pt1.y - r + ydiff,
                      pt2.x + xdiff, pt2.y + r + ydiff)

        if self.format == 'SVG':
            from blockdiag.imagedraw.simplesvg import pathdata

            path = pathdata(box[0], box[1])
            path.line(box[2], box[1])
            path.ellarc(r // 2, r, 0, 0, 1, box[2], box[3])
            path.line(box[0], box[3])
            path.ellarc(r // 2, r, 0, 0, 1, box[0], box[1])

            if shadow:
                self.drawer.path(path, fill=self.shadow, filter='blur')
            else:
                self.drawer.path(path, fill=network.color,
                                 outline=network.linecolor)

                path = pathdata(box[2], box[3])
                path.ellarc(r // 2, r, 0, 0, 1, box[2], box[1])
                self.drawer.path(path, fill='none', outline=network.linecolor)

                # for edge jumping
                line = (XY(box[0], box[1]), XY(box[2], box[1]))
                self.drawer.line(line, fill='none', jump=True)
        else:
            lsection = Box(box[0] - r // 2, box[1], box[0] + r // 2, box[3])
            rsection = Box(box[2] - r // 2, box[1], box[2] + r // 2, box[3])

            if shadow:
                color = self.shadow
                _filter = 'blur'
            else:
                color = network.color
                _filter = None

            # fill background
            self.drawer.rectangle(box, outline=color,
                                  fill=color, filter=_filter)
            self.drawer.ellipse(lsection, outline=color,
                                fill=color, filter=_filter)
            self.drawer.ellipse(rsection, outline=color,
                                fill=color, filter=_filter)

            if not shadow:
                upper = (XY(box[0], box[1]), XY(box[2], box[1]))
                self.drawer.line(upper, fill=network.linecolor, jump=True)

                bottom = (XY(box[0], box[3]), XY(box[2], box[3]))
                self.drawer.line(bottom, fill=network.linecolor, jump=True)

                self.drawer.arc(lsection, 90, 270, fill=network.linecolor)
                self.drawer.ellipse(rsection, outline=network.linecolor,
                                    fill=network.color)

    def _draw_elements(self):
        self.trunklines()

        for network in self.diagram.networks:
            self.trunkline_label(network)

        super(DiagramDraw, self)._draw_elements()

        ####################
        # draw routes

        metrics = self.metrics

        diameter = metrics.trunk_diameter
        pad_unit = diameter // 2

        def top_below(p):
            # virtical offset from top of network trunk for "below"
            return diameter + pad_unit * p

        def bottom_below(p):
            # virtical offset from bottom of network trunk for "below"
            return pad_unit * p

        def top_above(p):
            # virtical offset from top of network trunk for "above"
            return - bottom_below(p)

        def bottom_above(p):
            # virtical offset from bottom of network trunk for "above"
            return - top_below(p)

        def right(p):
            # horizontal offset from a connector line for "right"
            return pad_unit * p

        def left(p):
            # horizontal offset from a connector line for "left"
            return - right(p)

        # values are tuple of functions to calculate below:
        # - horizontal offset from a connector line
        # - vertical offset from bottom of network trunk
        # - vertical offset from top of network trunk
        offset_funcs = {
            'la': (left, bottom_above, top_above),
            'lb': (left, bottom_below, top_below),
            'ra': (right, bottom_above, top_above),
            'rb': (right, bottom_below, top_below),
        }

        cell = metrics.cellsize

        def down_head(node, hoff):
            xy = metrics.node(node).top
            return (XY(xy.x + hoff, xy.y - 1),
                    XY(xy.x + hoff - cell // 2, xy.y - cell),
                    XY(xy.x + hoff + cell // 2, xy.y - cell),
                    XY(xy.x + hoff, xy.y - 1))

        def up_head(node, hoff):
            xy = metrics.node(node).bottom
            return (XY(xy.x + hoff, xy.y + 1),
                    XY(xy.x + hoff - cell // 2, xy.y + cell),
                    XY(xy.x + hoff + cell // 2, xy.y + cell),
                    XY(xy.x + hoff, xy.y + 1))

        for route in self.diagram.routes:
            node1 = route.node1  # "from" node
            node2 = route.node2  # "to" node

            network = list(set(node1.networks) & set(node2.networks))[0]

            def get_line(node):
                # get the line of the connector belonging to common network
                for connector in metrics.node(node).connectors:
                    if _deautoscaler(connector.network) is network:
                        return connector.line

            offsets = [func(route.pad) for func in offset_funcs[route.path]]
            hoff, voff_bottom, voff_top = offsets

            edges = []

            # In nwdaig, y coordinates of each connector lines are
            # direction insensitive: y of "from" (= line[0].y) is
            # always less than y of "to" (= line[1].y).
            #
            # On the other hand, routing is direction sensitive.
            # Therefore, checking and reordering are needed, in order
            # to get below:
            #
            # - line as an edge along network trunk
            # - direction of "arrow head"

            line = get_line(node1)
            if network.xy.y <= node1.xy.y:
                # "line" is connected from "(bottom of) network"(=
                # line[0]) to "(top of) node" (= line[1])
                edges.append((XY(line[1].x + hoff, line[1].y),
                              XY(line[0].x + hoff, line[0].y + voff_bottom)))
            else:
                # "line" is connected from "(bottom of) node" (=
                # line[0]) to "(top of) network" (= line[1])
                edges.append((XY(line[0].x + hoff, line[0].y),
                              XY(line[1].x + hoff, line[1].y + voff_top)))

            line = get_line(node2)
            if network.xy.y <= node2.xy.y:
                # "line" is connected from "(bottom of) network" (=
                # line[0]) to "(top of) node" (= line[1])
                edges.append((XY(line[0].x + hoff, line[0].y + voff_bottom),
                              XY(line[1].x + hoff, line[1].y)))
                head = down_head
            else:
                # "line" is connected from "(bottom of) node" (=
                # line[0]) to "(top of) network" (= line[1])
                edges.append((XY(line[1].x + hoff, line[1].y + voff_top),
                              XY(line[0].x + hoff, line[0].y)))
                head = up_head

            # Now, each location tuples in "edges" are direction
            # sensitive. Therefore, line as an edge along network trunk
            # can be derived easily: from "the end of the 1st edge" to
            # "the begging of the 2nd edge".
            edges[1:1] = [(edges[0][1], edges[1][0])]

            for edge in edges:
                self.drawer.line(edge, style=route.style,
                                 fill=route.color, thick=route.thick)

            self.drawer.polygon(head(node2, hoff),
                                outline=route.color, fill=route.color)

    def trunkline_label(self, network):
        if network.display_label:
            m = self.metrics.network(network)
            self.drawer.textarea(m.textbox, network.display_label,
                                 self.metrics.font_for(network),
                                 fill=network.textcolor, halign="right")

    def node(self, node, **kwargs):
        m = self.metrics

        for connector in m.node(node).connectors:
            self.draw_connector(connector)
            network = _deautoscaler(connector.network)

            if network in node.address:
                label = node.address[network]
                self.drawer.textarea(connector.textbox, label,
                                     self.metrics.font_for(node),
                                     fill=node.textcolor, halign="left")

        super(DiagramDraw, self).node(node, **kwargs)

    def draw_connector(self, connector):
        network = _deautoscaler(connector.network)
        if (network.trunk_diameter):
            r = int(network.trunk_diameter) // 2
        else:
            r = self.metrics.trunk_diameter // 2
        
        #jump_radius = r + 5
        #jump_shift = r
        #self.drawer.set_options(jump_forward='vertical',
        #                    jump_radius=jump_radius,
        #                    jump_shift=jump_shift)
        #print(f"jump_radius={jump_radius}, jump_shift={jump_shift}")
        self.drawer.line(connector.line, fill=network.linecolor, jump=True)

    def group_label(self, group):
        if group.label:
            m = self.metrics.cell(group)
            self.drawer.textarea(m.grouplabelbox, group.label,
                                 self.metrics.font_for(group),
                                 valign='top', fill=group.textcolor)
