from ..Qt import QtGui, QtCore
from ..Point import Point
from .GraphicsObject import GraphicsObject
from .TextItem import TextItem
from .ViewBox import ViewBox
from .. import functions as fn
import numpy as np
import weakref


__all__ = ['InfiniteLine']


class InfiniteLine(GraphicsObject):
    """
    **Bases:** :class:`GraphicsObject <pyqtgraph.GraphicsObject>`

    Displays a line of infinite length.
    This line may be dragged to indicate a position in data coordinates.

    =============================== ===================================================
    **Signals:**
    sigDragged(self)
    sigPositionChangeFinished(self)
    sigPositionChanged(self)
    =============================== ===================================================
    """

    sigDragged = QtCore.Signal(object)
    sigPositionChangeFinished = QtCore.Signal(object)
    sigPositionChanged = QtCore.Signal(object)

    def __init__(self, pos=None, angle=90, pen=None, movable=False, bounds=None,
                 hoverPen=None, label=False, textColor=None, textFill=None,
                 textPosition=[0.05, 0.5], textFormat="{:.3f}", draggableLabel=False,
                 suffix=None, name='InfiniteLine'):
        """
        =============== ==================================================================
        **Arguments:**
        pos             Position of the line. This can be a QPointF or a single value for
                        vertical/horizontal lines.
        angle           Angle of line in degrees. 0 is horizontal, 90 is vertical.
        pen             Pen to use when drawing line. Can be any arguments that are valid
                        for :func:`mkPen <pyqtgraph.mkPen>`. Default pen is transparent
                        yellow.
        movable         If True, the line can be dragged to a new position by the user.
        hoverPen        Pen to use when drawing line when hovering over it. Can be any
                        arguments that are valid for :func:`mkPen <pyqtgraph.mkPen>`.
                        Default pen is red.
        bounds          Optional [min, max] bounding values. Bounds are only valid if the
                        line is vertical or horizontal.
        label           if True, a label is displayed next to the line to indicate its
                        location in data coordinates
        textColor       color of the label. Can be any argument fn.mkColor can understand.
        textFill        A brush to use when filling within the border of the text.
        textPosition    list of float (0-1) that defines when the precise location of the
                        label. The first float governs the location of the label in the
                        direction of the line, whereas the second one governs the shift
                        of the label from one side of the line to the other in the
                        orthogonal direction.
        textFormat      Any new python 3 str.format() format.
        draggableLabel  Bool. If True, the user can relocate the label during the dragging.
                        If set to True, the first entry of textPosition is no longer
                        useful.
        suffix          If not None, corresponds to the unit to show next to the label
        name            name of the item
        =============== ==================================================================
        """

        GraphicsObject.__init__(self)

        if bounds is None:              ## allowed value boundaries for orthogonal lines
            self.maxRange = [None, None]
        else:
            self.maxRange = bounds
        self.moving = False
        self.setMovable(movable)
        self.mouseHovering = False
        self.p = [0, 0]
        self.setAngle(angle)

        if textColor is None:
            textColor = (200, 200, 100)
        self.textColor = textColor
        self.textFill = textFill
        self.textPosition = textPosition
        self.suffix = suffix


        self.textItem = InfLineLabel(self, fill=textFill)
        self.textItem.setParentItem(self)
        self.setDraggableLabel(draggableLabel)
        self.showLabel(label)

        self.anchorLeft = (1., 0.5)
        self.anchorRight = (0., 0.5)
        self.anchorUp = (0.5, 1.)
        self.anchorDown = (0.5, 0.)

        if pos is None:
            pos = Point(0,0)
        self.setPos(pos)

        if pen is None:
            pen = (200, 200, 100)
        self.setPen(pen)
        if hoverPen is None:
            self.setHoverPen(color=(255,0,0), width=self.pen.width())
        else:
            self.setHoverPen(hoverPen)
        self.currentPen = self.pen

        self.format = textFormat

        self._name = name

        # Cache complex value for drawing speed-up (#PR267)
        self._line = None
        self._boundingRect = None

    def setMovable(self, m):
        """Set whether the line is movable by the user."""
        self.movable = m
        self.setAcceptHoverEvents(m)

    def setBounds(self, bounds):
        """Set the (minimum, maximum) allowable values when dragging."""
        self.maxRange = bounds
        self.setValue(self.value())

    def setPen(self, *args, **kwargs):
        """Set the pen for drawing the line. Allowable arguments are any that are valid
        for :func:`mkPen <pyqtgraph.mkPen>`."""
        self.pen = fn.mkPen(*args, **kwargs)
        if not self.mouseHovering:
            self.currentPen = self.pen
            self.update()

    def setHoverPen(self, *args, **kwargs):
        """Set the pen for drawing the line while the mouse hovers over it.
        Allowable arguments are any that are valid
        for :func:`mkPen <pyqtgraph.mkPen>`.

        If the line is not movable, then hovering is also disabled.

        Added in version 0.9.9."""
        self.hoverPen = fn.mkPen(*args, **kwargs)
        if self.mouseHovering:
            self.currentPen = self.hoverPen
            self.update()

    def setAngle(self, angle):
        """
        Takes angle argument in degrees.
        0 is horizontal; 90 is vertical.

        Note that the use of value() and setValue() changes if the line is
        not vertical or horizontal.
        """
        self.angle = ((angle+45) % 180) - 45   ##  -45 <= angle < 135
        self.resetTransform()
        self.rotate(self.angle)
        self.update()

    def setPos(self, pos):

        if type(pos) in [list, tuple]:
            newPos = pos
        elif isinstance(pos, QtCore.QPointF):
            newPos = [pos.x(), pos.y()]
        else:
            if self.angle == 90:
                newPos = [pos, 0]
            elif self.angle == 0:
                newPos = [0, pos]
            else:
                raise Exception("Must specify 2D coordinate for non-orthogonal lines.")

        ## check bounds (only works for orthogonal lines)
        if self.angle == 90:
            if self.maxRange[0] is not None:
                newPos[0] = max(newPos[0], self.maxRange[0])
            if self.maxRange[1] is not None:
                newPos[0] = min(newPos[0], self.maxRange[1])
        elif self.angle == 0:
            if self.maxRange[0] is not None:
                newPos[1] = max(newPos[1], self.maxRange[0])
            if self.maxRange[1] is not None:
                newPos[1] = min(newPos[1], self.maxRange[1])

        if self.p != newPos:
            self.p = newPos
            self._invalidateCache()
            GraphicsObject.setPos(self, Point(self.p))
            self.sigPositionChanged.emit(self)

    def getXPos(self):
        return self.p[0]

    def getYPos(self):
        return self.p[1]

    def getPos(self):
        return self.p

    def value(self):
        """Return the value of the line. Will be a single number for horizontal and
        vertical lines, and a list of [x,y] values for diagonal lines."""
        if self.angle%180 == 0:
            return self.getYPos()
        elif self.angle%180 == 90:
            return self.getXPos()
        else:
            return self.getPos()

    def setValue(self, v):
        """Set the position of the line. If line is horizontal or vertical, v can be
        a single value. Otherwise, a 2D coordinate must be specified (list, tuple and
        QPointF are all acceptable)."""
        self.setPos(v)

    ## broken in 4.7
    #def itemChange(self, change, val):
        #if change in [self.ItemScenePositionHasChanged, self.ItemSceneHasChanged]:
            #self.updateLine()
            #print "update", change
            #print self.getBoundingParents()
        #else:
            #print "ignore", change
        #return GraphicsObject.itemChange(self, change, val)

    def _invalidateCache(self):
        self._line = None
        self._boundingRect = None

    def boundingRect(self):
        if self._boundingRect is None:
            #br = UIGraphicsItem.boundingRect(self)
            br = self.viewRect()
            ## add a 4-pixel radius around the line for mouse interaction.

            px = self.pixelLength(direction=Point(1,0), ortho=True)  ## get pixel length orthogonal to the line
            if px is None:
                px = 0
            w = (max(4, self.pen.width()/2, self.hoverPen.width()/2)+1) * px
            br.setBottom(-w)
            br.setTop(w)
            br = br.normalized()
            self._boundingRect = br
            self._line = QtCore.QLineF(br.right(), 0.0, br.left(), 0.0)
        return self._boundingRect

    def paint(self, p, *args):
        p.setPen(self.currentPen)
        p.drawLine(self._line)

    def dataBounds(self, axis, frac=1.0, orthoRange=None):
        if axis == 0:
            return None   ## x axis should never be auto-scaled
        else:
            return (0,0)

    def mouseDragEvent(self, ev):
        if self.movable and ev.button() == QtCore.Qt.LeftButton:
            if ev.isStart():
                self.moving = True
                self.cursorOffset = self.pos() - self.mapToParent(ev.buttonDownPos())
                self.startPosition = self.pos()
            ev.accept()

            if not self.moving:
                return

            self.setPos(self.cursorOffset + self.mapToParent(ev.pos()))
            self.sigDragged.emit(self)
            if ev.isFinish():
                self.moving = False
                self.sigPositionChangeFinished.emit(self)

    def mouseClickEvent(self, ev):
        if self.moving and ev.button() == QtCore.Qt.RightButton:
            ev.accept()
            self.setPos(self.startPosition)
            self.moving = False
            self.sigDragged.emit(self)
            self.sigPositionChangeFinished.emit(self)

    def hoverEvent(self, ev):
        if (not ev.isExit()) and self.movable and ev.acceptDrags(QtCore.Qt.LeftButton):
            self.setMouseHover(True)
        else:
            self.setMouseHover(False)

    def setMouseHover(self, hover):
        ## Inform the item that the mouse is (not) hovering over it
        if self.mouseHovering == hover:
            return
        self.mouseHovering = hover
        if hover:
            self.currentPen = self.hoverPen
        else:
            self.currentPen = self.pen
        self.update()

    def viewTransformChanged(self):
        """
        Called whenever the transformation matrix of the view has changed.
        (eg, the view range has changed or the view was resized)
        """
        self._invalidateCache()
        self.textItem.updatePosition()

    def showLabel(self, state):
        """
        Display or not the label indicating the location of the line in data
        coordinates.

        ==============   ======================================================
        **Arguments:**
        state            If True, the label is shown. Otherwise, it is hidden.
        ==============   ======================================================
        """
        self.textItem.setVisible(state)

    def setTextLocation(self, position=0.05, shift=0.5):
        """
        Set the parameters that defines the location of the label on the axis.
        The position *parameter* governs the location of the label in the
        direction of the line, whereas the *shift* governs the shift of the
        label from one side of the line to the other in the orthogonal
        direction.

        ==============   ======================================================
        **Arguments:**
        position          float (range of value = [0-1])
        shift             float (range of value = [0-1]).
        ==============   ======================================================
        """
        self.textItem.orthoPos = position
        self.textItem.shiftPos = shift
        self.textItem.updatePosition()

    def setDraggableLabel(self, state):
        """
        Set the state of the label regarding its behaviour during the dragging
        of the line. If True, then the location of the label change during the
        dragging of the line.
        """
        self.textItem.setMovable(state)

    def setName(self, name):
        self._name = name

    def name(self):
        return self._name


class InfLineLabel(TextItem):
    # a text label that attaches itself to an InfiniteLine
    def __init__(self, line, **kwds):
        self.line = line
        self.movable = False
        self.dragAxis = None  # 0=x, 1=y
        self.orthoPos = 0.5  # text will always be placed on the line at a position relative to view bounds
        self.format = "{value}"
        self.line.sigPositionChanged.connect(self.valueChanged)
        TextItem.__init__(self, **kwds)
        self.valueChanged()

    def valueChanged(self):
        if not self.isVisible():
            return
        value = self.line.value()
        self.setText(self.format.format(value=value))
        self.updatePosition()
    
    def updatePosition(self):
        view = self.getViewBox()
        if not self.isVisible() or not isinstance(view, ViewBox):
            # not in a viewbox, skip update
            return
        
        # 1. determine view extents along line axis
        tr = view.childGroup.itemTransform(self.line)[0]
        vr = tr.mapRect(view.viewRect())
        pt1 = Point(vr.left(), 0)
        pt2 = Point(vr.right(), 0)
        
        # 2. pick relative point between extents and set position
        pt = pt2 * self.orthoPos + pt1 * (1-self.orthoPos)
        self.setPos(pt)
        
    def setVisible(self, v):
        TextItem.setVisible(self, v)
        if v:
            self.updateText()
            self.updatePosition()
            
    def setMovable(self, m):
        self.movable = m
        self.setAcceptHoverEvents(m)
        
    def mouseDragEvent(self, ev):
        if self.movable and ev.button() == QtCore.Qt.LeftButton:
            if ev.isStart():
                self._moving = True
                self._cursorOffset = self._posToRel(ev.buttonDownPos())
                self._startPosition = self.orthoPos
            ev.accept()

            if not self._moving:
                return

            rel = self._posToRel(ev.pos())
            self.orthoPos = self._startPosition + rel - self._cursorOffset
            self.updatePosition()
            if ev.isFinish():
                self._moving = False

    def mouseClickEvent(self, ev):
        if self.moving and ev.button() == QtCore.Qt.RightButton:
            ev.accept()
            self.orthoPos = self._startPosition
            self.moving = False

    def hoverEvent(self, ev):
        if not ev.isExit() and self.movable:
            ev.acceptDrags(QtCore.Qt.LeftButton)

    def _posToRel(self, pos):
        # convert local position to relative position along line between view bounds
        view = self.getViewBox()
        tr = view.childGroup.itemTransform(self.line)[0]
        vr = tr.mapRect(view.viewRect())
        pos = self.mapToParent(pos)
        return (pos.x() - vr.left()) / vr.width()
        
        