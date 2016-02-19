from ..Qt import QtCore, QtGui
from ..Point import Point
from .UIGraphicsItem import *
from .. import functions as fn

class TextItem(UIGraphicsItem):
    """
    GraphicsItem displaying unscaled text (the text will always appear normal even inside a scaled ViewBox). 
    """
    def __init__(self, text='', color=(200,200,200), html=None, anchor=(0,0), border=None, fill=None, angle=0):
        """
        ==============  =================================================================================
        **Arguments:**
        *text*          The text to display
        *color*         The color of the text (any format accepted by pg.mkColor)
        *html*          If specified, this overrides both *text* and *color*
        *anchor*        A QPointF or (x,y) sequence indicating what region of the text box will
                        be anchored to the item's position. A value of (0,0) sets the upper-left corner
                        of the text box to be at the position specified by setPos(), while a value of (1,1)
                        sets the lower-right corner.
        *border*        A pen to use when drawing the border
        *fill*          A brush to use when filling within the border
        ==============  =================================================================================
        """
        
        ## not working yet
        #*angle*      Angle in degrees to rotate text (note that the rotation assigned in this item's 
                     #transformation will be ignored)
                     
        self.anchor = Point(anchor)
        #self.angle = 0
        UIGraphicsItem.__init__(self)
        self.textItem = QtGui.QGraphicsTextItem()
        self.textItem.setParentItem(self)
        self._lastTransform = None
        self._bounds = QtCore.QRectF()
        if html is None:
            self.setText(text, color)
        else:
            self.setHtml(html)
        self.fill = fn.mkBrush(fill)
        self.border = fn.mkPen(border)
        self.setAngle(angle)
        #self.textItem.setFlag(self.ItemIgnoresTransformations)  ## This is required to keep the text unscaled inside the viewport

    def setText(self, text, color=(200,200,200)):
        """
        Set the text and color of this item. 
        
        This method sets the plain text of the item; see also setHtml().
        """
        color = fn.mkColor(color)
        self.textItem.setDefaultTextColor(color)
        self.textItem.setPlainText(text)
        self.updateText()
        #html = '<span style="color: #%s; text-align: center;">%s</span>' % (color, text)
        #self.setHtml(html)
        
    def updateAnchor(self):
        pass
        #self.resetTransform()
        #self.translate(0, 20)
        
    def setPlainText(self, *args):
        """
        Set the plain text to be rendered by this item. 
        
        See QtGui.QGraphicsTextItem.setPlainText().
        """
        self.textItem.setPlainText(*args)
        self.updateText()
        
    def setHtml(self, *args):
        """
        Set the HTML code to be rendered by this item. 
        
        See QtGui.QGraphicsTextItem.setHtml().
        """
        self.textItem.setHtml(*args)
        self.updateText()
        
    def setTextWidth(self, *args):
        """
        Set the width of the text.
        
        If the text requires more space than the width limit, then it will be
        wrapped into multiple lines.
        
        See QtGui.QGraphicsTextItem.setTextWidth().
        """
        self.textItem.setTextWidth(*args)
        self.updateText()
        
    def setFont(self, *args):
        """
        Set the font for this text. 
        
        See QtGui.QGraphicsTextItem.setFont().
        """
        self.textItem.setFont(*args)
        self.updateText()
        
    def setAngle(self, angle):
        self.textItem.resetTransform()
        self.textItem.rotate(angle)
        self.updateText()
        
    def updateText(self):
        # update text position to obey anchor
        r = self.textItem.boundingRect()
        tl = self.textItem.mapToParent(r.topLeft())
        br = self.textItem.mapToParent(r.bottomRight())
        offset = (br - tl) * self.anchor
        self.textItem.setPos(-offset)
        
        ### Needed to maintain font size when rendering to image with increased resolution
        #self.textItem.resetTransform()
        ##self.textItem.rotate(self.angle)
        #if self._exportOpts is not False and 'resolutionScale' in self._exportOpts:
            #s = self._exportOpts['resolutionScale']
            #self.textItem.scale(s, s)
        
    def viewRangeChanged(self):
        self.updateText()

    def boundingRect(self):
        return self.textItem.mapToParent(self.textItem.boundingRect()).boundingRect()

    def viewTransformChanged(self):
        # called whenever view transform has changed.
        # Do this here to avoid double-updates when view changes.
        self.updateTransform()
        
    def paint(self, p, *args):
        # this is not ideal because it causes another update to be scheduled.
        # ideally, we would have a sceneTransformChanged event to react to..
        self.updateTransform()
        
        if self.border.style() != QtCore.Qt.NoPen or self.fill.style() != QtCore.Qt.NoBrush:
            p.setPen(self.border)
            p.setBrush(self.fill)
            p.setRenderHint(p.Antialiasing, True)
            p.drawPolygon(self.textItem.mapToParent(self.textItem.boundingRect()))
        
    def updateTransform(self):
        # update transform such that this item has the correct orientation
        # and scaling relative to the scene, but inherits its position from its
        # parent.
        # This is similar to setting ItemIgnoresTransformations = True, but 
        # does not break mouse interaction and collision detection.
        p = self.parentItem()
        if p is None:
            pt = QtGui.QTransform()
        else:
            pt = p.sceneTransform()
        
        if pt == self._lastTransform:
            return

        t = pt.inverted()[0]
        # reset translation
        t.setMatrix(t.m11(), t.m12(), t.m13(), t.m21(), t.m22(), t.m23(), 0, 0, t.m33())
        self.setTransform(t)
        
        self._lastTransform = pt
        